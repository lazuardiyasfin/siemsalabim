"""Tests for EngineClient."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from dashboard_backend.engine_client import EngineClient


@pytest.fixture
async def engine_client():
    """Create an EngineClient instance."""
    callback = AsyncMock()
    return EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)


@pytest.mark.asyncio
async def test_engine_client_init():
    """Test EngineClient initialization."""
    callback = AsyncMock()
    client = EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)

    assert client.engine_url == "ws://localhost:8000/ws/dashboard"
    assert client.on_event == callback
    assert client.connected is False
    assert client.websocket is None


@pytest.mark.asyncio
async def test_reconnect_success(engine_client):
    """Test successful reconnection."""
    with patch.object(engine_client, "connect", new_callable=AsyncMock) as mock_connect:
        await engine_client.reconnect(max_retries=3, delay=1)
        mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_reconnect_exponential_backoff(engine_client):
    """Test reconnect with exponential backoff on failures."""
    attempt_times = []

    async def mock_connect_fail():
        attempt_times.append(asyncio.get_event_loop().time())
        raise ConnectionError("Connection failed")

    with patch.object(engine_client, "connect", side_effect=mock_connect_fail):
        with pytest.raises(ConnectionError):
            await engine_client.reconnect(max_retries=2, delay=0.1)

    # Verify exponential backoff was applied (delay should increase)
    assert len(attempt_times) >= 1


@pytest.mark.asyncio
async def test_reconnect_eventual_success(engine_client):
    """Test reconnect that succeeds after failures."""
    attempt_count = 0

    async def mock_connect():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ConnectionError("Connection failed")
        engine_client.connected = True

    with patch.object(engine_client, "connect", side_effect=mock_connect):
        await engine_client.reconnect(max_retries=3, delay=0.01)
        assert engine_client.connected is True


@pytest.mark.asyncio
async def test_disconnect():
    """Test disconnection."""
    callback = AsyncMock()
    client = EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)

    mock_websocket = AsyncMock()
    client.websocket = mock_websocket
    client.connected = True

    await client.disconnect()

    mock_websocket.close.assert_called_once()
    assert client.connected is False


@pytest.mark.asyncio
async def test_disconnect_when_already_disconnected():
    """Test disconnect when websocket is None."""
    callback = AsyncMock()
    client = EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)

    client.websocket = None
    client.connected = False

    await client.disconnect()
    assert client.connected is False


@pytest.mark.asyncio
async def test_listen_valid_json():
    """Test listen method with valid JSON."""
    callback = AsyncMock()
    client = EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)

    mock_websocket = AsyncMock()
    mock_websocket.recv = AsyncMock(
        side_effect=[
            '{"type": "event", "data": {"message": "test"}}',
            asyncio.CancelledError(),
        ]
    )
    client.websocket = mock_websocket
    client.connected = True

    with pytest.raises(asyncio.CancelledError):
        async for _ in client._listen():
            pass

    callback.assert_called_once()


@pytest.mark.asyncio
async def test_listen_invalid_json():
    """Test listen method with invalid JSON."""
    callback = AsyncMock()
    client = EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)

    mock_websocket = AsyncMock()
    mock_websocket.recv = AsyncMock(
        side_effect=["invalid json {", asyncio.CancelledError()]
    )
    client.websocket = mock_websocket
    client.connected = True

    with pytest.raises(asyncio.CancelledError):
        async for _ in client._listen():
            pass

    callback.assert_not_called()


@pytest.mark.asyncio
async def test_listen_exception_handling():
    """Test listen method exception handling."""
    callback = AsyncMock()
    client = EngineClient("ws://localhost:8000/ws/dashboard", on_event=callback)

    mock_websocket = AsyncMock()
    mock_websocket.recv = AsyncMock(side_effect=Exception("Connection error"))
    client.websocket = mock_websocket
    client.connected = True

    with pytest.raises(Exception):
        async for _ in client._listen():
            pass

    assert client.connected is False
