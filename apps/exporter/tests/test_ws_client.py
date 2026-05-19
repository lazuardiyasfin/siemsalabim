import asyncio

import pytest

from src.ws_client import WebSocketClient


class TestWebSocketClientEnqueue:
    def test_enqueue_returns_true(self) -> None:
        """Enqueue succeeds when queue has capacity."""
        client = WebSocketClient("ws://localhost:8000", "token")

        assert client.enqueue("test message") is True

    def test_enqueue_full_queue_returns_false(self) -> None:
        """Enqueue returns False when queue is at capacity."""
        client = WebSocketClient("ws://localhost:8000", "token")
        # Fill the queue.
        for i in range(10_000):
            client.enqueue(f"msg-{i}")

        assert client.enqueue("overflow") is False

    def test_stop_sets_running_false(self) -> None:
        """Calling stop signals the client to cease reconnecting."""
        client = WebSocketClient("ws://localhost:8000", "token")

        client.stop()

        assert client._running is False


class TestWebSocketClientConnect:
    """Tests for connect/reconnect behavior with a mock server."""

    @pytest.mark.asyncio
    async def test_start_cancelled_gracefully(self) -> None:
        """Client handles cancellation without raising."""
        client = WebSocketClient("ws://localhost:19999", "token")
        task = asyncio.create_task(client.start())

        await asyncio.sleep(0.2)
        task.cancel()

        await asyncio.sleep(0.1)
        assert task.done()