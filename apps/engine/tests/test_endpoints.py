import os

import pytest

os.environ.setdefault("SIEM_INGEST_TOKEN", "testtoken123")

from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health check returns 200 with ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWebSocketIngest:
    """Tests for /ws/ingest WebSocket endpoint."""

    def test_valid_auth_accepts_connection(self, client: TestClient) -> None:
        """Valid bearer token allows WebSocket connection."""
        with client.websocket_connect(
            "/ws/ingest",
            headers={"Authorization": "Bearer testtoken123"},
        ) as ws:
            ws.send_json(
                {
                    "exporter_id": "test",
                    "host": "test-host",
                    "path": "/var/log/auth.log",
                    "line": "2026-05-20T04:03:49.940072+00:00 siem-target sshd[1234]: Invalid user admin from 1.2.3.4 port 22",
                    "received_at": "2026-05-20T04:03:50Z",
                }
            )

    def test_invalid_auth_closes_connection(self, client: TestClient) -> None:
        """Invalid bearer token closes WebSocket with 1008."""
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/ws/ingest",
                headers={"Authorization": "Bearer wrongtoken"},
            ) as ws:
                ws.receive_text()

    def test_missing_auth_closes_connection(self, client: TestClient) -> None:
        """Missing auth header closes WebSocket with 1008."""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/ingest") as ws:
                ws.receive_text()

    def test_malformed_json_closes_connection(self, client: TestClient) -> None:
        """Malformed JSON payload closes connection with 1003."""
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/ws/ingest",
                headers={"Authorization": "Bearer testtoken123"},
            ) as ws:
                ws.send_json({"bad": "data"})
                ws.receive_text()

    def test_sshd_event_triggers_alert(self, client: TestClient) -> None:
        """SSH invalid user event is processed without error."""
        with client.websocket_connect(
            "/ws/ingest",
            headers={"Authorization": "Bearer testtoken123"},
        ) as ws:
            ws.send_json(
                {
                    "exporter_id": "test",
                    "host": "siem-target",
                    "path": "/var/log/auth.log",
                    "line": "2026-05-20T04:03:49.940072+00:00 siem-target sshd[1234]: Invalid user hacker from 9.8.7.6 port 22",
                    "received_at": "2026-05-20T04:03:50Z",
                }
            )

    def test_nginx_event_processed(self, client: TestClient) -> None:
        """Nginx access log event is processed without error."""
        with client.websocket_connect(
            "/ws/ingest",
            headers={"Authorization": "Bearer testtoken123"},
        ) as ws:
            ws.send_json(
                {
                    "exporter_id": "test",
                    "host": "siem-target",
                    "path": "/var/log/nginx/access.log",
                    "line": '185.177.72.16 - - [19/May/2026:21:46:44 +0000] "GET /.git/config HTTP/1.1" 404 134 "-" "curl/8.7.1"',
                    "received_at": "2026-05-20T04:03:50Z",
                }
            )

    def test_unparseable_line_does_not_crash(self, client: TestClient) -> None:
        """Unparseable log line is handled gracefully."""
        with client.websocket_connect(
            "/ws/ingest",
            headers={"Authorization": "Bearer testtoken123"},
        ) as ws:
            ws.send_json(
                {
                    "exporter_id": "test",
                    "host": "test",
                    "path": "/tmp/random.log",
                    "line": "this is not a valid log line at all",
                    "received_at": "2026-05-20T04:03:50Z",
                }
            )
