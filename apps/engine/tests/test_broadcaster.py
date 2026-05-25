import pytest
from unittest.mock import AsyncMock, MagicMock

from src.broadcaster import EventBroadcaster


class TestEventBroadcaster:
    """Tests for EventBroadcaster connection management."""

    def test_initial_count_zero(self) -> None:
        """New broadcaster has zero connections."""
        b = EventBroadcaster()

        assert b.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_connect_increments_count(self) -> None:
        """Connecting a WebSocket increments count."""
        b = EventBroadcaster()
        ws = AsyncMock()

        await b.connect(ws)

        assert b.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_disconnect_decrements_count(self) -> None:
        """Disconnecting a WebSocket decrements count."""
        b = EventBroadcaster()
        ws = AsyncMock()

        await b.connect(ws)
        b.disconnect(ws)

        assert b.get_connection_count() == 0

    def test_disconnect_unknown_ws(self) -> None:
        """Disconnecting unknown WebSocket does not crash."""
        b = EventBroadcaster()
        ws = MagicMock()

        b.disconnect(ws)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self) -> None:
        """Broadcast sends message to all connected clients."""
        b = EventBroadcaster()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await b.connect(ws1)
        await b.connect(ws2)
        await b.broadcast({"type": "test", "data": "hello"})

        assert ws1.send_json.called or ws1.send_text.called
        assert ws2.send_json.called or ws2.send_text.called
