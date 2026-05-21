import asyncio
import json
import logging
from typing import Callable, Optional

import websockets

logger = logging.getLogger(__name__)


# WebSocket client for receiving real-time events from the engine
class EngineClient:

    def __init__(self, engine_url: str, on_event: Optional[Callable] = None):
        self.engine_url = engine_url
        self.on_event = on_event
        self.connected = False
        self.websocket = None

    # Connect to the engine and start receiving events
    async def connect(self) -> None:
        try:
            self.websocket = await websockets.connect(self.engine_url)
            self.connected = True
            logger.info("Connected to engine at %s", self.engine_url)
            await self._listen()
        except Exception as exc:
            logger.error("Failed to connect to engine: %s", exc)
            self.connected = False
            raise

    # Listen for messages from the engine
    async def _listen(self) -> None:
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "event" and self.on_event:
                        await self.on_event(data.get("data"))
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON from engine: %s", message)
        except Exception as exc:
            logger.error("Error listening to engine: %s", exc)
            self.connected = False

    # Disconnect from the engine
    async def disconnect(self) -> None:
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from engine")

    # Reconnect to the engine with exponential backoff
    async def reconnect(self, max_retries: int = 5, delay: int = 5) -> None:
        for attempt in range(max_retries):
            try:
                await self.connect()
                return
            except Exception as exc:
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    logger.warning(
                        "Reconnect attempt %d failed. Retrying in %d seconds...",
                        attempt + 1,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Failed to reconnect after %d attempts", max_retries)
                    raise
