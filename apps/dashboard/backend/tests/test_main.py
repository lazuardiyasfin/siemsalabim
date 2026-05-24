import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from dashboard_backend.main import app, config
from dashboard_backend.state import DashboardState

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_broadcast_to_frontends_empty():
    """Test broadcast to frontends when no frontends connected."""
    from dashboard_backend.workers import broadcast_to_frontends

    mock_state = MagicMock()
    mock_state.connected_frontends = set()

    # Should not raise even with no frontends
    await broadcast_to_frontends(mock_state, {"type": "ALERT", "data": {}})


@pytest.mark.asyncio
async def test_broadcast_to_frontends_with_clients():
    """Test broadcast to multiple frontends."""
    from dashboard_backend.workers import broadcast_to_frontends

    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    mock_state = MagicMock()
    mock_state.connected_frontends = {mock_ws1, mock_ws2}

    event = {"type": "ALERT", "data": {"message": "test"}}
    await broadcast_to_frontends(mock_state, event)

    mock_ws1.send_json.assert_called_once_with(event)
    mock_ws2.send_json.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_broadcast_handles_disconnected_client():
    """Test broadcast removes disconnected clients."""
    from dashboard_backend.workers import broadcast_to_frontends

    mock_ws_good = AsyncMock()
    mock_ws_bad = AsyncMock()
    mock_ws_bad.send_json = AsyncMock(side_effect=Exception("Client disconnected"))

    mock_state = MagicMock()
    mock_state.connected_frontends = {mock_ws_good, mock_ws_bad}

    event = {"type": "ALERT", "data": {}}
    await broadcast_to_frontends(mock_state, event)

    assert mock_ws_good in mock_state.connected_frontends
    assert mock_ws_bad not in mock_state.connected_frontends


@pytest.mark.asyncio
async def test_lifespan_startup():
    """Test lifespan context manager startup."""
    from dashboard_backend.main import lifespan

    test_app = FastAPI()

    async def dummy_worker(*args, **kwargs):
        pass

    with (
        patch("dashboard_backend.main.EngineClient") as mock_client_class,
        patch("dashboard_backend.main.eps_broadcast_worker", side_effect=dummy_worker),
        patch(
            "dashboard_backend.main.exporter_monitor_worker", side_effect=dummy_worker
        ),
        patch("dashboard_backend.main.close_geoip_reader"),
    ):
        mock_instance = AsyncMock()
        mock_instance.reconnect = AsyncMock()
        mock_client_class.return_value = mock_instance

        async with lifespan(test_app):
            assert isinstance(test_app.state.live_state, DashboardState)


@pytest.mark.asyncio
async def test_lifespan_shutdown():
    """Test lifespan context manager shutdown sequence."""
    from dashboard_backend.main import lifespan

    test_app = FastAPI()
    mock_engine_instance = AsyncMock()

    async def dummy_worker(*args, **kwargs):
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

    with (
        patch("dashboard_backend.main.EngineClient", return_value=mock_engine_instance),
        patch("dashboard_backend.main.eps_broadcast_worker", side_effect=dummy_worker),
        patch(
            "dashboard_backend.main.exporter_monitor_worker", side_effect=dummy_worker
        ),
        patch("dashboard_backend.main.close_geoip_reader") as mock_close_geoip,
    ):
        async with lifespan(test_app):
            pass

    mock_close_geoip.assert_called_once()
    mock_engine_instance.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_cancellation_reraised():
    """Test that CancelledError during gather bubbles up correctly."""
    from dashboard_backend.main import lifespan

    test_app = FastAPI()
    mock_engine_instance = AsyncMock()

    with (
        patch("dashboard_backend.main.EngineClient", return_value=mock_engine_instance),
        patch("dashboard_backend.main.eps_broadcast_worker"),
        patch("dashboard_backend.main.exporter_monitor_worker"),
        patch("dashboard_backend.main.close_geoip_reader"),
        patch(
            "dashboard_backend.main.asyncio.gather", side_effect=asyncio.CancelledError
        ),
    ):
        with pytest.raises(asyncio.CancelledError):
            async with lifespan(test_app):
                pass


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    if not hasattr(app.state, "live_state"):
        app.state.live_state = DashboardState()

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_stats_endpoint():
    """Test stats endpoint metrics mapping."""
    mock_engine_instance = AsyncMock()
    mock_engine_instance.connected = True

    with patch(
        "dashboard_backend.main.EngineClient", return_value=mock_engine_instance
    ):
        with TestClient(app) as client:
            # Inject the mock frontend directly into the active state lifecycle loop
            client.app.state.live_state.connected_frontends.clear()
            mock_ws = AsyncMock()
            client.app.state.live_state.connected_frontends.add(mock_ws)

            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert "connected_frontends" in data
            assert "engine_connected" in data
            assert data["connected_frontends"] == 1
            assert data["engine_connected"] is True


@pytest_asyncio.fixture
async def client():
    """Fixture providing an HTTPX AsyncClient instance."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as ac:
        yield ac


@pytest.fixture
def mock_config():
    """Fixture providing the application configuration instance."""
    return config


@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient, mock_config):
    """Should return username only if HttpOnly cookie is valid."""
    from dashboard_backend.security import create_access_token

    token = create_access_token(
        data={"sub": mock_config.user}, secret_key=mock_config.jwt_secret_key
    )

    client.cookies.set("access_token", token)
    response = await client.get("/api/auth/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"username": mock_config.user}


@pytest.mark.asyncio
async def test_get_current_user_missing_token(client: AsyncClient):
    """Should return 401 status if cookie does not include token."""
    response = await client.get("/api/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "No token found"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Should return 401 status if token is invalid."""
    client.cookies.set("access_token", "token_asal_asalan_atau_invalid")
    response = await client.get("/api/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_get_historical_alerts_success(client: AsyncClient, mock_config):
    """Should forward historical alerts payload when upstream engine responds with 200 OK."""
    from dashboard_backend.security import create_access_token

    token = create_access_token(
        data={"sub": mock_config.user}, secret_key=mock_config.jwt_secret_key
    )
    client.cookies.set("access_token", token)

    mock_alerts = [{"id": 1, "rule_id": "brute_force", "severity": "HIGH"}]
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_alerts

    # Setup the internal client mock
    mock_inner_client = AsyncMock()
    mock_inner_client.get.return_value = mock_response

    # Setup the async context manager wrappers
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_inner_client)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    # Patch only where AsyncClient is instantiated inside main.py
    with patch(
        "dashboard_backend.main.httpx.AsyncClient", return_value=mock_client_instance
    ):
        response = await client.get("/api/alerts?limit=5&severity=HIGH")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_alerts
        mock_inner_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_historical_alerts_upstream_error(client: AsyncClient, mock_config):
    """Should return 502 Bad Gateway if the upstream engine encounters an internal server error."""
    from dashboard_backend.security import create_access_token

    token = create_access_token(
        data={"sub": mock_config.user}, secret_key=mock_config.jwt_secret_key
    )
    client.cookies.set("access_token", token)

    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_inner_client = AsyncMock()
    mock_inner_client.get.return_value = mock_response

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_inner_client)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "dashboard_backend.main.httpx.AsyncClient", return_value=mock_client_instance
    ):
        response = await client.get("/api/alerts")

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert (
            response.json()["detail"]
            == "Invalid data state signature received from upstream service."
        )


@pytest.mark.asyncio
async def test_get_historical_alerts_network_failure(client: AsyncClient, mock_config):
    """Should return 503 Service Unavailable if communication with the engine fails at the network layer."""
    from dashboard_backend.security import create_access_token

    token = create_access_token(
        data={"sub": mock_config.user}, secret_key=mock_config.jwt_secret_key
    )
    client.cookies.set("access_token", token)

    # Create a dummy request object to prevent the internal httpx property error
    mock_request = httpx.Request("GET", "http://localhost:8000/api/alerts")

    mock_inner_client = AsyncMock()
    mock_inner_client.get.side_effect = httpx.RequestError(
        "Connection refused", request=mock_request
    )

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_inner_client)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "dashboard_backend.main.httpx.AsyncClient", return_value=mock_client_instance
    ):
        response = await client.get("/api/alerts")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert (
            response.json()["detail"]
            == "Upstream log orchestration interface is temporarily unreachable."
        )


@pytest.mark.asyncio
async def test_get_historical_alerts_unauthorized(client: AsyncClient):
    """Should reject incoming traffic with 401 Unauthorized if the required session token is omitted."""
    response = await client.get("/api/alerts")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "No token found"
