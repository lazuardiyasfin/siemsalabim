import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ExporterManager:
    """Track connected exporter WebSocket connections."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    def register(self, exporter_id: str, websocket: WebSocket) -> None:
        """Register an exporter connection."""
        self._connections[exporter_id] = websocket
        logger.info("Exporter registered: %s", exporter_id)

    def unregister(self, exporter_id: str) -> None:
        """Remove an exporter connection."""
        self._connections.pop(exporter_id, None)
        logger.info("Exporter unregistered: %s", exporter_id)

    def get_exporter_ids(self) -> list[str]:
        """Return list of connected exporter IDs."""
        return list(self._connections.keys())

    async def send_command(self, exporter_id: str, command: dict[str, object]) -> bool:
        """Send a command to a specific exporter. Returns True if sent."""
        ws = self._connections.get(exporter_id)
        if ws is None:
            logger.warning("Exporter not connected: %s", exporter_id)
            return False

        try:
            await ws.send_text(json.dumps(command))
            logger.info(
                "Sent command '%s' to exporter '%s'.", command.get("type"), exporter_id
            )
            return True
        except Exception as exc:
            logger.warning("Failed to send command to %s: %s", exporter_id, exc)
            return False
