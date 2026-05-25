import logging
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .broadcaster import EventBroadcaster
from .config import EngineConfig
from .exporter_manager import ExporterManager
from .ingest import ingest_handler
from .parser import init_parser
from .parser.decoders import reload_decoders
from .rules import RuleEngine

config = EngineConfig()

logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

broadcaster = EventBroadcaster()
exporter_mgr = ExporterManager()

rules_dir = Path(__file__).parent.parent / "rules"
decoders_dir = Path(__file__).parent.parent / "decoders"

rule_engine = RuleEngine(rules_dir)
init_parser(decoders_dir)


app = FastAPI(title="siemsalabim-engine", version="0.1.0")


# ---- Request/response models ----


class AddLogPathRequest(BaseModel):
    """Request body for adding a log path."""

    exporter_id: str = Field(description="Target exporter to add the path to.")
    path: str = Field(description="Log file path to watch.")


class AddLogPathResponse(BaseModel):
    """Response for add log path."""

    status: str
    message: str


# ---- HTTP endpoints ----


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/stats")
async def stats() -> dict[str, int]:
    """Engine statistics."""
    return {"active_dashboards": broadcaster.get_connection_count()}


@app.post("/rules/reload")
async def reload_rules() -> dict[str, object]:
    """Hot-reload rule definitions from YAML files."""
    count = rule_engine.reload()
    logger.info("Rules reloaded: %d rule(s) active.", count)
    return {"status": "ok", "rules_loaded": count}


@app.post("/decoders/reload")
async def reload_decoders_endpoint() -> dict[str, object]:
    """Hot-reload decoder definitions from YAML files."""
    count = reload_decoders(decoders_dir)
    logger.info("Decoders reloaded: %d decoder(s) active.", count)
    return {"status": "ok", "decoders_loaded": count}


@app.get("/api/log-paths")
async def get_log_paths() -> dict[str, object]:
    """List connected exporters."""
    return {
        "status": "ok",
        "exporters": exporter_mgr.get_exporter_ids(),
    }


@app.post("/api/log-paths")
async def add_log_path(request: AddLogPathRequest) -> AddLogPathResponse:
    """Send add_path command to a connected exporter."""
    command = {"type": "add_path", "path": request.path}
    sent = await exporter_mgr.send_command(request.exporter_id, command)

    if sent:
        return AddLogPathResponse(
            status="ok",
            message=f"Path '{request.path}' sent to exporter '{request.exporter_id}'.",
        )

    return AddLogPathResponse(
        status="error",
        message=f"Exporter '{request.exporter_id}' not connected.",
    )


# ---- WebSocket endpoints ----


@app.websocket("/ws/ingest")
async def ws_ingest(websocket: WebSocket) -> None:
    """WebSocket endpoint for log ingestion from exporters."""
    await ingest_handler(websocket, config, rule_engine, broadcaster, exporter_mgr)


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
