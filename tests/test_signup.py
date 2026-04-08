"""Tests for the signup endpoint and activity management"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client with a fresh app instance"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities database before each test"""
    from src.app import activities
    
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Swimming Club": {
            "description": "Swimming training and water sports",
            "schedule": "Mondays and Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Art Studio": {
            "description": "Express creativity through painting and drawing",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Drama Club": {
            "description": "Theater arts and performance training",
            "schedule": "Tuesdays, 4:00 PM - 6:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Debate Team": {
            "description": "Learn public speaking and argumentation skills",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": []
        },
        "Science Club": {
            "description": "Hands-on experiments and scientific exploration",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        }
    }
    
    # Clear and reset
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


# ====== HAPPY PATH TESTS ======

def test_successful_signup(client):
    """Test successful signup for an activity with available spots"""
    response = client.post(
        "/activities/Basketball Team/signup?email=alice@mergington.edu"
    )
    
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert "alice@mergington.edu" in response.json()["message"]


def test_successful_signup_adds_participant(client):
    """Test that successful signup actually adds participant to the activity"""
    from src.app import activities
    
    initial_count = len(activities["Swimming Club"]["participants"])
    
    response = client.post(
        "/activities/Swimming Club/signup?email=bob@mergington.edu"
    )
    
    assert response.status_code == 200
    assert len(activities["Swimming Club"]["participants"]) == initial_count + 1
    assert "bob@mergington.edu" in activities["Swimming Club"]["participants"]


# ====== ERROR CASE TESTS ======

def test_activity_not_found(client):
    """Test signup fails with 404 when activity doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=test@mergington.edu"
    )
    
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_duplicate_registration_prevented(client):
    """Test that same student cannot register twice for same activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )
    
    assert response.status_code == 400
    assert "already signed up for this activity" in response.json()["detail"]


def test_capacity_limit_enforced(client):
    """Test that activity rejects signup when at max capacity"""
    from src.app import activities
    
    # Create an activity at capacity
    activities["Test Activity"] = {
        "description": "Test",
        "schedule": "Monday, 1:00 PM",
        "max_participants": 2,
        "participants": ["person1@test.edu", "person2@test.edu"]
    }
    
    response = client.post(
        "/activities/Test Activity/signup?email=person3@test.edu"
    )
    
    assert response.status_code == 400
    assert "maximum capacity" in response.json()["detail"]


def test_schedule_conflict_prevention(client):
    """Test that student cannot sign up for activities at same time"""
    # michael@mergington.edu is already in Chess Club (Fridays, 3:30 PM - 5:00 PM)
    # Try to sign up for Science Club (also Fridays, 3:30 PM - 5:00 PM)
    
    response = client.post(
        "/activities/Science Club/signup?email=michael@mergington.edu"
    )
    
    assert response.status_code == 400
    assert "already signed up for another activity at the same time" in response.json()["detail"]


def test_multiple_activities_different_times_allowed(client):
    """Test that student can sign up for multiple activities at different times"""
    from src.app import activities
    
    # michael@mergington.edu is in Chess Club (Fridays, 3:30 PM - 5:00 PM)
    # Try to sign up for Swimming Club (Mondays and Wednesdays, 3:30 PM - 5:00 PM)
    # These don't overlap, so it should succeed
    
    response = client.post(
        "/activities/Swimming Club/signup?email=michael@mergington.edu"
    )
    
    assert response.status_code == 200
    assert "michael@mergington.edu" in activities["Swimming Club"]["participants"]


# ====== GET ACTIVITIES TESTS ======

def test_get_activities_returns_all(client):
    """Test that GET /activities returns all activities"""
    response = client.get("/activities")
    
    assert response.status_code == 200
    activities_data = response.json()
    assert len(activities_data) == 9
    assert "Chess Club" in activities_data
    assert "Basketball Team" in activities_data


def test_get_activities_includes_participant_count(client):
    """Test that activities endpoint includes current participants"""
    response = client.get("/activities")
    
    activities_data = response.json()
    chess_club = activities_data["Chess Club"]
    
    assert "participants" in chess_club
    assert len(chess_club["participants"]) == 2
    assert "michael@mergington.edu" in chess_club["participants"]


# ====== ROOT REDIRECT TEST ======

def test_root_redirects_to_static(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    
    assert response.status_code == 307  # Temporary redirect
    assert "/static/index.html" in response.headers["location"]
