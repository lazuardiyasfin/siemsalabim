import json
import aiosqlite
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends

from .broadcaster import EventBroadcaster
from .config import EngineConfig
from .database import init_db, get_db
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

rules_dir = Path(__file__).parent.parent / "rules"
decoders_dir = Path(__file__).parent.parent / "decoders"

rule_engine = RuleEngine(rules_dir)
init_parser(decoders_dir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown tasks."""
    try:
        await init_db()
        logger.info("Database verification and table creation complete.")
    except Exception as e:
        logger.error(f"Critical error during database initialization: {e}")
        raise e
    yield


app = FastAPI(title="siemsalabim-engine", version="0.1.0", lifespan=lifespan)


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


@app.websocket("/ws/ingest")
async def ws_ingest(websocket: WebSocket) -> None:
    """WebSocket endpoint for log ingestion from exporters."""
    await ingest_handler(websocket, config, rule_engine, broadcaster)


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


@app.get("/api/alerts")
async def get_historical_alerts(
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
    range: str = "1h",
    severity: str | None = None,
) -> list[dict]:
    """Exposes structured historical alert logs filtered by relative time ranges."""

    range_mapping = {
        "1h": "-1 hours",
        "24h": "-24 hours",
        "7d": "-7 days",
        "30d": "-30 days",
    }
    time_modifier = range_mapping.get(range, "-24 hours")

    if severity:
        query = (
            "SELECT * FROM alerts "
            "WHERE timestamp >= datetime('now', ?) AND severity = ? "
            "ORDER BY timestamp DESC;"
        )
        params = (time_modifier, severity.upper())
    else:
        query = (
            "SELECT * FROM alerts "
            "WHERE timestamp >= datetime('now', ?) "
            "ORDER BY timestamp DESC;"
        )
        params = (time_modifier,)

    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()

    return [
        {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "rule_id": row["rule_id"],
            "rule_name": row["rule_name"],
            "severity": row["severity"],
            "description": row["description"],
            "event_count": row["event_count"],
            "source_events": json.loads(row["source_events"]),
        }
        for row in rows
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
