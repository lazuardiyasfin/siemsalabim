from dashboard_backend.main import app

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect


MOCK_PASSWORD = "admin123"


@pytest.fixture
def client():
    """Fixture to provide a TestClient with lifespan execution."""
    with TestClient(app) as c:
        yield c


def test_login_success(client):
    """Test successful admin login via HttpOnly cookie."""
    response = client.post(
        "/login", data={"username": "admin", "password": MOCK_PASSWORD}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    # Verify that the access_token cookie is set by the backend
    assert "access_token" in response.cookies


def test_websocket_missing_token(client):
    """Test that WebSocket connection is rejected when token cookie is missing."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/events") as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 1008


def test_websocket_invalid_token(client):
    """Test that WebSocket connection is rejected with an invalid token cookie."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        # Pass invalid token via cookies dictionary
        with client.websocket_connect("/ws/events", cookies={"access_token": "invalid_value"}) as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 1008


def test_websocket_success(client):
    """Test successful WebSocket connection with a valid JWT token cookie."""
    # Perform login to automatically populate cookies in the client session
    login_response = client.post(
        "/login", data={"username": "admin", "password": MOCK_PASSWORD}
    )
    token = login_response.cookies.get("access_token")

    # Connect to WebSocket; TestClient automatically forwards session cookies
    with client.websocket_connect("/ws/events", cookies={"access_token": token}) as websocket:
        websocket.send_text("ping")