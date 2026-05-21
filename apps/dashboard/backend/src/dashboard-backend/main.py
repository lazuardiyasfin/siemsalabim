import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .config import DashboardConfig
from .engine_client import EngineClient

config = DashboardConfig()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)

engine_client: EngineClient | None = None
connected_frontends: Set[WebSocket] = set()


async def broadcast_to_frontends(event: dict) -> None:
    """Broadcast event from engine to all connected frontends."""
    disconnected = set()

    for websocket in connected_frontends:
        try:
            await websocket.send_json(event)
        except Exception as exc:
            logger.warning("Failed to send event to frontend: %s", exc)
            disconnected.add(websocket)

    for websocket in disconnected:
        connected_frontends.discard(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global engine_client

    logger.info("Starting dashboard backend...")

    async def on_engine_event(event: dict) -> None:
        """Handle event from engine."""
        await broadcast_to_frontends(event)

    engine_client = EngineClient(config.engine_url, on_event=on_engine_event)
    engine_task = asyncio.create_task(engine_client.reconnect(max_retries=5))

    yield

    logger.info("Shutting down dashboard backend...")
    engine_task.cancel()
    try:
        await engine_task
    except asyncio.CancelledError:
        raise
    finally:
        if engine_client:
            await engine_client.disconnect()


app = FastAPI(
    title="siemsalabim-dashboard",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/stats")
async def stats() -> dict:
    """Dashboard statistics."""
    return {
        "connected_frontends": len(connected_frontends),
        "engine_connected": engine_client.connected if engine_client else False,
    }


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    """WebSocket endpoint for frontend to receive real-time events from engine."""
    await websocket.accept()
    connected_frontends.add(websocket)
    logger.info("Frontend connected. Total frontends: %d", len(connected_frontends))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_frontends.discard(websocket)
        logger.info(
            "Frontend disconnected. Total frontends: %d", len(connected_frontends)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dashboard-backend.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )
