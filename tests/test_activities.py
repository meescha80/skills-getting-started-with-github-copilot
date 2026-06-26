import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Fixture to restore the in-memory `activities` before each test (Arrange)

    We deepcopy the initial state and restore it so tests are hermetic.
    """
    original = copy.deepcopy(app_module.activities)
    yield
    # Teardown: restore the original state
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities_returns_expected_structure():
    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_adds_participant():
    activity = "Chess Club"
    email = "testuser@example.com"

    # Ensure precondition
    assert email not in app_module.activities[activity]["participants"]

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    assert email in app_module.activities[activity]["participants"]


def test_signup_duplicate_returns_400():
    activity = "Programming Class"
    email = "duplicate@example.com"

    # Arrange: first signup succeeds
    resp1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp1.status_code == 200

    # Act: second signup should fail
    resp2 = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp2.status_code == 400


def test_signup_fails_when_activity_is_full():
    activity = "Chess Club"

    # Fill the activity to capacity
    app_module.activities[activity]["participants"] = [f"user{i}@example.com" for i in range(app_module.activities[activity]["max_participants"])]
    email = "overflow@example.com"

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Activity is full"


def test_unregister_participant_removes_entry():
    activity = "Gym Class"
    email = "removable@example.com"

    # Arrange: sign up the participant first
    resp_signup = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp_signup.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    # Act: unregister
    resp_del = client.delete(f"/activities/{activity}/participants?email={email}")

    # Assert
    assert resp_del.status_code == 200
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_missing_returns_404():
    activity = "Math Olympiad"
    email = "notexist@example.com"

    # Ensure precondition: email not in list
    assert email not in app_module.activities[activity]["participants"]

    # Act
    resp = client.delete(f"/activities/{activity}/participants?email={email}")

    # Assert
    assert resp.status_code == 404
