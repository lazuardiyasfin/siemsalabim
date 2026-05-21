import logging
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .broadcaster import EventBroadcaster
from .config import EngineConfig
from .ingest import ingest_handler

config = EngineConfig()

logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

broadcaster = EventBroadcaster()

app = FastAPI(title="siemsalabim-engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/stats")
async def stats() -> dict[str, int]:
    """Engine statistics."""
    return {"active_dashboards": broadcaster.get_connection_count()}


@app.websocket("/ws/ingest")
async def ws_ingest(websocket: WebSocket) -> None:
    """WebSocket endpoint for log ingestion from exporters."""
    await ingest_handler(websocket, config, broadcaster)


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket) -> None:
    """WebSocket endpoint for dashboards to receive real-time events."""
    await broadcaster.connect(websocket)
    logger.info("Dashboard subscribed to events")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
        logger.info("Dashboard unsubscribed from events")
