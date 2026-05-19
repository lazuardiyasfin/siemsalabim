import logging
import sys

from fastapi import FastAPI, WebSocket

from .config import EngineConfig
from .ingest import ingest_handler

config = EngineConfig()

logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

app = FastAPI(title="siemsalabim-engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.websocket("/ws/ingest")
async def ws_ingest(websocket: WebSocket) -> None:
    """WebSocket endpoint for log ingestion from exporters."""
    await ingest_handler(websocket, config)