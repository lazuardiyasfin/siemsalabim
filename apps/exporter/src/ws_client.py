import asyncio
import logging

import websockets
from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)

MAX_QUEUE_SIZE: int = 10_000
BACKOFF_BASE: float = 1.0
BACKOFF_MAX: float = 60.0


class WebSocketClient:
    def __init__(self, url: str, token: str) -> None:
        self._url = url
        self._token = token
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self._running = False

    def enqueue(self, message: str) -> bool:
        try:
            self._queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.warning("Send queue full (%d), dropping message.", MAX_QUEUE_SIZE)
            return False

    async def start(self) -> None:
        self._running = True
        backoff = BACKOFF_BASE

        while self._running:
            try:
                conn = await self._connect()
                backoff = BACKOFF_BASE
                await self._send_loop(conn)
            except (
                websockets.ConnectionClosed,
                websockets.InvalidHandshake,
                OSError,
            ) as exc:
                logger.warning("WebSocket connection lost: %s", exc)
            except asyncio.CancelledError:
                logger.info("WebSocket client cancelled, shutting down.")
                return

            if not self._running:
                break

            logger.info("Reconnecting in %.1fs...", backoff)
            try:
                await asyncio.sleep(backoff)
            except asyncio.CancelledError:
                return
            backoff = min(backoff * 2, BACKOFF_MAX)

    def stop(self) -> None:
        self._running = False

    async def _connect(self) -> ClientConnection:
        extra_headers = {"Authorization": f"Bearer {self._token}"}
        conn = await websockets.connect(
            self._url,
            additional_headers=extra_headers,
        )
        logger.info("Connected to %s.", self._url)
        return conn

    async def _send_loop(self, conn: ClientConnection) -> None:
        try:
            while self._running:
                message = await self._queue.get()
                await conn.send(message)
                self._queue.task_done()
        finally:
            await conn.close()
