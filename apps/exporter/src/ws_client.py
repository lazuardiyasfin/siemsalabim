import asyncio
import json
import logging
from collections.abc import Callable

import websockets
from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)

MAX_QUEUE_SIZE: int = 10_000
BACKOFF_BASE: float = 1.0
BACKOFF_MAX: float = 60.0

CommandCallback = Callable[[dict[str, object]], None]


class WebSocketClient:
    """Async WebSocket client with automatic reconnection."""

    def __init__(
        self,
        url: str,
        token: str,
        command_callback: CommandCallback | None = None,
    ) -> None:
        self._url = url
        self._token = token
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self._running = False
        self._on_command = command_callback

    def enqueue(self, message: str) -> bool:
        """Add a message to the send queue."""
        try:
            self._queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.warning("Send queue full (%d), dropping message.", MAX_QUEUE_SIZE)
            return False

    async def start(self) -> None:
        """Connect and send/receive loop. Reconnects with exponential backoff."""
        self._running = True
        backoff = BACKOFF_BASE

        while self._running:
            try:
                conn = await self._connect()
                backoff = BACKOFF_BASE
                await self._run_loops(conn)
            except (
                websockets.ConnectionClosed,
                websockets.InvalidHandshake,
                OSError,
            ) as exc:
                logger.warning("WebSocket connection lost: %s", exc)
            except asyncio.CancelledError:
                logger.info("WebSocket client cancelled, shutting down.")
                raise

            if not self._running:
                break

            logger.info("Reconnecting in %.1fs...", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX)

    def stop(self) -> None:
        """Signal the client to stop reconnecting."""
        self._running = False

    async def _connect(self) -> ClientConnection:
        """Open a WebSocket connection with auth header."""
        extra_headers = {"Authorization": f"Bearer {self._token}"}
        conn = await websockets.connect(
            self._url,
            additional_headers=extra_headers,
        )
        logger.info("Connected to %s.", self._url)
        return conn

    async def _run_loops(self, conn: ClientConnection) -> None:
        """Run send and receive loops concurrently."""
        send = asyncio.create_task(self._send_loop(conn))
        recv = asyncio.create_task(self._receive_loop(conn))
        try:
            await asyncio.gather(send, recv)
        finally:
            send.cancel()
            recv.cancel()
            await conn.close()

    async def _send_loop(self, conn: ClientConnection) -> None:
        """Drain the queue and send messages over *conn*."""
        while self._running:
            message = await self._queue.get()
            await conn.send(message)
            self._queue.task_done()

    async def _receive_loop(self, conn: ClientConnection) -> None:
        """Listen for incoming commands from the engine."""
        async for raw in conn:
            if self._on_command is None:
                continue
            try:
                command = json.loads(raw)
                logger.info("Received command: %s", command.get("type", "unknown"))
                self._on_command(command)
            except (json.JSONDecodeError, AttributeError) as exc:
                logger.warning("Invalid command received: %s", exc)
