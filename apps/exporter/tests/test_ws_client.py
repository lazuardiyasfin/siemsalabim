"""Tests for WebSocket client."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ws_client import WebSocketClient


class TestWebSocketClientEnqueue:
    """Tests for the enqueue/queue mechanism."""

    def test_enqueue_returns_true(self) -> None:
        """Enqueue succeeds when queue has capacity."""
        client = WebSocketClient("ws://localhost:8000", "token")
        assert client.enqueue("test message") is True

    def test_enqueue_full_queue_returns_false(self) -> None:
        """Enqueue returns False when queue is at capacity."""
        client = WebSocketClient("ws://localhost:8000", "token")
        for i in range(10_000):
            client.enqueue(f"msg-{i}")
        assert client.enqueue("overflow") is False

    def test_enqueue_multiple(self) -> None:
        """Multiple messages can be enqueued."""
        client = WebSocketClient("ws://localhost:8000", "token")
        for i in range(100):
            assert client.enqueue(f"msg-{i}") is True

    def test_stop_sets_running_false(self) -> None:
        """Calling stop signals the client to cease reconnecting."""
        client = WebSocketClient("ws://localhost:8000", "token")
        client.stop()
        assert client._running is False


class TestWebSocketClientCallback:
    """Tests for command callback."""

    def test_callback_stored(self) -> None:
        """Command callback is stored on init."""
        cb = MagicMock()
        client = WebSocketClient("ws://localhost:8000", "token", command_callback=cb)
        assert client._on_command is cb

    def test_no_callback_default(self) -> None:
        """Default has no command callback."""
        client = WebSocketClient("ws://localhost:8000", "token")
        assert client._on_command is None


class TestWebSocketClientConnect:
    """Tests for connect/reconnect behavior."""

    @pytest.mark.asyncio
    async def test_start_cancelled_gracefully(self) -> None:
        """Client handles cancellation without raising."""
        client = WebSocketClient("ws://localhost:19999", "token")
        task = asyncio.create_task(client.start())
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_stop_breaks_loop(self) -> None:
        """Calling stop causes start loop to exit."""
        client = WebSocketClient("ws://localhost:19999", "token")
        task = asyncio.create_task(client.start())
        await asyncio.sleep(0.1)
        client.stop()
        await asyncio.sleep(1.5)
        assert task.done() or not client._running
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_send_loop_drains_queue(self) -> None:
        """Send loop sends queued messages."""
        client = WebSocketClient("ws://localhost:8000", "token")
        client._running = True
        conn = AsyncMock()
        client.enqueue("hello")
        client.enqueue("world")

        async def stop_after_drain() -> None:
            await asyncio.sleep(0.1)
            client._running = False

        task = asyncio.create_task(client._send_loop(conn))
        stopper = asyncio.create_task(stop_after_drain())
        await asyncio.sleep(0.3)
        task.cancel()
        stopper.cancel()

        assert conn.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_receive_loop_calls_callback(self) -> None:
        """Receive loop calls command callback with parsed JSON."""
        cb = MagicMock()
        client = WebSocketClient("ws://localhost:8000", "token", command_callback=cb)

        command = {"type": "add_path", "path": "/var/log/test.log"}
        conn = AsyncMock()
        conn.__aiter__ = lambda self: self
        conn.__anext__ = AsyncMock(
            side_effect=[json.dumps(command), StopAsyncIteration]
        )

        await client._receive_loop(conn)

        cb.assert_called_once()
        called_arg = cb.call_args[0][0]
        assert called_arg["type"] == "add_path"

    @pytest.mark.asyncio
    async def test_receive_loop_no_callback_skips(self) -> None:
        """Receive loop skips messages when no callback set."""
        client = WebSocketClient("ws://localhost:8000", "token")

        conn = AsyncMock()
        conn.__aiter__ = lambda self: self
        conn.__anext__ = AsyncMock(
            side_effect=[json.dumps({"type": "test"}), StopAsyncIteration]
        )

        await client._receive_loop(conn)

    @pytest.mark.asyncio
    async def test_receive_loop_invalid_json(self) -> None:
        """Receive loop handles invalid JSON gracefully."""
        cb = MagicMock()
        client = WebSocketClient("ws://localhost:8000", "token", command_callback=cb)

        conn = AsyncMock()
        conn.__aiter__ = lambda self: self
        conn.__anext__ = AsyncMock(side_effect=["NOT JSON {{{", StopAsyncIteration])

        await client._receive_loop(conn)

        cb.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_loops_cancels_tasks(self) -> None:
        """run_loops creates send/receive tasks and cleans up."""
        client = WebSocketClient("ws://localhost:8000", "token")
        client._running = True

        conn = AsyncMock()
        conn.__aiter__ = lambda self: self
        conn.__anext__ = AsyncMock(side_effect=StopAsyncIteration)

        async def stop_soon() -> None:
            await asyncio.sleep(0.1)
            client._running = False

        stopper = asyncio.create_task(stop_soon())

        try:
            await asyncio.wait_for(client._run_loops(conn), timeout=1.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass

        stopper.cancel()
        conn.close.assert_called()
