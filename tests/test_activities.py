import pytest


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Check that we have all activities
    assert len(activities) == 10
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Gym Class" in activities
    
    # Check Chess Club details
    chess = activities["Chess Club"]
    assert chess["description"] == "Learn strategies and compete in chess tournaments"
    assert chess["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert chess["max_participants"] == 12
    assert len(chess["participants"]) == 2


def test_get_specific_activity(client):
    """Test getting a specific activity"""
    response = client.get("/activities/Chess%20Club")
    assert response.status_code == 200
    activity = response.json()
    
    assert activity["description"] == "Learn strategies and compete in chess tournaments"
    assert activity["max_participants"] == 12
    assert "michael@mergington.edu" in activity["participants"]
    assert "daniel@mergington.edu" in activity["participants"]


def test_get_activity_not_found(client):
    """Test getting a non-existent activity"""
    response = client.get("/activities/Nonexistent%20Club")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_for_activity(client):
    """Test signing up for an activity"""
    response = client.post(
        "/activities/Basketball%20Team/signup?email=student@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up student@mergington.edu for Basketball Team" in data["message"]
    
    # Verify participant was added
    activity_response = client.get("/activities/Basketball%20Team")
    activity = activity_response.json()
    assert "student@mergington.edu" in activity["participants"]


def test_signup_duplicate_participant(client):
    """Test that duplicate signups are prevented"""
    # First signup
    response1 = client.post(
        "/activities/Basketball%20Team/signup?email=student@mergington.edu"
    )
    assert response1.status_code == 200
    
    # Attempt duplicate signup
    response2 = client.post(
        "/activities/Basketball%20Team/signup?email=student@mergington.edu"
    )
    assert response2.status_code == 400
    assert "already signed up" in response2.json()["detail"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/Fake%20Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_remove_participant(client):
    """Test removing a participant from an activity"""
    # First, verify initial state
    activity_response = client.get("/activities/Chess%20Club")
    initial_participants = activity_response.json()["participants"]
    assert "michael@mergington.edu" in initial_participants
    
    # Remove participant
    response = client.delete(
        "/activities/Chess%20Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Removed michael@mergington.edu from Chess Club" in data["message"]
    
    # Verify participant was removed
    activity_response = client.get("/activities/Chess%20Club")
    activity = activity_response.json()
    assert "michael@mergington.edu" not in activity["participants"]


def test_remove_nonexistent_participant(client):
    """Test removing a participant that's not signed up"""
    response = client.delete(
        "/activities/Chess%20Club/signup?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_remove_from_nonexistent_activity(client):
    """Test removing a participant from a non-existent activity"""
    response = client.delete(
        "/activities/Fake%20Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_activity_availability_updates(client):
    """Test that availability counts update correctly"""
    # Get initial availability
    response1 = client.get("/activities/Basketball%20Team")
    initial_spots = (
        response1.json()["max_participants"] - len(response1.json()["participants"])
    )
    
    # Sign up a new participant
    client.post("/activities/Basketball%20Team/signup?email=new@mergington.edu")
    
    # Check updated availability
    response2 = client.get("/activities/Basketball%20Team")
    updated_spots = (
        response2.json()["max_participants"] - len(response2.json()["participants"])
    )
    
    assert updated_spots == initial_spots - 1
