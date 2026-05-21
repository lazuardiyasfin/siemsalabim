"""Event broadcaster for real-time dashboard updates."""

import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


# Manages WebSocket connections and broadcasts events to all connected dashboards
class EventBroadcaster:

    def __init__(self):
        """Initialize the broadcaster."""
        self.active_connections: Set[WebSocket] = set()

    # Register a new dashboard connection
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("Dashboard connected. Total connections: %d", len(self.active_connections))

    # Unregister a dashboard connection
    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("Dashboard disconnected. Total connections: %d", len(self.active_connections))

    # Send a message to all connected dashboards
    async def broadcast(self, message: dict) -> None:
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send to dashboard: %s", exc)
                disconnected.add(websocket)
        
        for websocket in disconnected:
            self.disconnect(websocket)

    # Get number of active dashboard connections
    def get_connection_count(self) -> int:
        return len(self.active_connections)
