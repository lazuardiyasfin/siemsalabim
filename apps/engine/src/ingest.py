import logging

from fastapi import WebSocket, WebSocketDisconnect

from .broadcaster import EventBroadcaster
from .config import EngineConfig
from .exporter_manager import ExporterManager
from .models import RawLog
from .parser import parse
from .rules import RuleEngine
from .rules.models import Alert

logger = logging.getLogger(__name__)

CLOSE_AUTH_FAIL = 1008
CLOSE_MALFORMED = 1003


async def verify_token(websocket: WebSocket, config: EngineConfig) -> bool:
    """Check Authorization header for a valid bearer token."""
    auth_header = websocket.headers.get("authorization", "")
    if auth_header == f"Bearer {config.ingest_token}":
        return True

    logger.warning("Auth failed from %s.", websocket.client)
    await websocket.close(code=CLOSE_AUTH_FAIL, reason="Invalid or missing token")
    return False


def _log_alerts(alerts: list[Alert], event_decoded: dict[str, object]) -> None:
    """Log each alert with severity and source info."""
    for alert in alerts:
        source = event_decoded.get("src_ip") or event_decoded.get("client_ip", "")
        logger.warning(
            "[ALERT][%s] %s — %s (source: %s)",
            alert.severity.upper(),
            alert.rule_name,
            alert.description,
            source,
        )


def _log_event(raw_log: RawLog, event_program: str, decoded: dict[str, object]) -> None:
    """Log a parsed event without alert."""
    logger.info(
        "[%s] %s → %s %s",
        raw_log.exporter_id,
        event_program,
        decoded.get("action", ""),
        {k: v for k, v in decoded.items() if k != "action"},
    )


async def _process_message(
    data: dict[str, object],
    rule_engine: RuleEngine,
    broadcaster: EventBroadcaster | None,
) -> None:
    """Parse a raw message, evaluate rules, and broadcast."""
    raw_log = RawLog(**data)
    event = parse(raw_log)

    if event is None:
        logger.debug("[%s] Unparseable: %s", raw_log.exporter_id, raw_log.line[:80])
        return

    alerts = rule_engine.evaluate(event)

    if alerts:
        _log_alerts(alerts, event.decoded)
        if broadcaster:
            for alert in alerts:
                await broadcaster.broadcast(
                    {"type": "alert", "data": alert.model_dump(mode="json")}
                )
    elif event.decoded:
        _log_event(raw_log, event.program, event.decoded)

    if broadcaster:
        await broadcaster.broadcast(
            {"type": "event", "data": event.model_dump(mode="json")}
        )


async def ingest_handler(
    websocket: WebSocket,
    config: EngineConfig,
    rule_engine: RuleEngine,
    broadcaster: EventBroadcaster | None = None,
    exporter_mgr: ExporterManager | None = None,
) -> None:
    """Handle a single exporter WebSocket connection."""
    await websocket.accept()

    if not await verify_token(websocket, config):
        return

    client = websocket.client
    exporter_id = ""
    logger.info("Exporter connected: %s", client)

    try:
        while True:
            data = await websocket.receive_json()
            try:
                if not exporter_id:
                    exporter_id = str(data.get("exporter_id", ""))
                    if exporter_id and exporter_mgr:
                        exporter_mgr.register(exporter_id, websocket)

                await _process_message(data, rule_engine, broadcaster)
            except Exception as exc:
                logger.warning("Malformed message from %s: %s", client, exc)
                await websocket.close(code=CLOSE_MALFORMED, reason="Malformed payload")
                return
    except WebSocketDisconnect:
        logger.info("Exporter disconnected: %s", client)
    finally:
        if exporter_id and exporter_mgr:
            exporter_mgr.unregister(exporter_id)
