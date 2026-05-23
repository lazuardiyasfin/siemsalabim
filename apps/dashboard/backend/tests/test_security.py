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
    """Test successful admin login."""
    response = client.post(
        "/login", 
        data={"username": "admin", "password": MOCK_PASSWORD}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_websocket_missing_token(client):
    """Test that WebSocket connection is rejected when token parameter is missing."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/events") as websocket:
            websocket.receive_text()  
    assert exc_info.value.code == 1008 


def test_websocket_invalid_token(client):
    """Test that WebSocket connection is rejected with an invalid token."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/events?token=invalid_token_value") as websocket:
            websocket.receive_text()  
    assert exc_info.value.code == 1008 


def test_websocket_success(client):
    """Test successful WebSocket connection with a valid JWT token."""
    login_response = client.post(
        "/login", 
        data={"username": "admin", "password": MOCK_PASSWORD}
    )
    token = login_response.json()["access_token"]

    with client.websocket_connect(f"/ws/events?token={token}") as websocket:
        websocket.send_text("ping")