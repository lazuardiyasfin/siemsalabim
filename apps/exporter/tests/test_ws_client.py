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


class TestWebSocketClientBiDirectional:
    """Tests for bi-directional WebSocket features."""

    def test_command_callback_stored(self) -> None:
        """Command callback is stored on init."""

        def my_callback(cmd: dict[str, object]) -> None:
            pass

        client = WebSocketClient(
            "ws://localhost:8000", "token", command_callback=my_callback
        )

        assert client._on_command is my_callback

    def test_no_callback_default(self) -> None:
        """Default has no command callback."""
        client = WebSocketClient("ws://localhost:8000", "token")

        assert client._on_command is None

    def test_enqueue_multiple(self) -> None:
        """Multiple messages can be enqueued."""
        client = WebSocketClient("ws://localhost:8000", "token")

        for i in range(100):
            assert client.enqueue(f"msg-{i}") is True

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        """Client can be stopped after start."""
        client = WebSocketClient("ws://localhost:19999", "token")
        task = asyncio.create_task(client.start())

        await asyncio.sleep(0.1)
        client.stop()
        await asyncio.sleep(0.2)

        assert not client._running
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
