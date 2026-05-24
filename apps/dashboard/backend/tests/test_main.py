import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
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
    """Fixture untuk menyediakan AsyncClient HTTPX."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as ac:
        yield ac


@pytest.fixture
def mock_config():
    """Fixture untuk menyediakan konfigurasi aplikasi."""
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
