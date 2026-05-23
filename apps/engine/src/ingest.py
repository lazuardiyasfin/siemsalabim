import logging

from fastapi import WebSocket, WebSocketDisconnect

from .broadcaster import EventBroadcaster
from .config import EngineConfig
from .models import RawLog
from .parser import parse
from .rules import RuleEngine

logger = logging.getLogger(__name__)

CLOSE_AUTH_FAIL = 1008
CLOSE_MALFORMED = 1003


async def verify_token(websocket: WebSocket, config: EngineConfig) -> bool:
    auth_header = websocket.headers.get("authorization", "")
    if auth_header == f"Bearer {config.ingest_token}":
        return True

    logger.warning("Auth failed from %s.", websocket.client)
    await websocket.close(code=CLOSE_AUTH_FAIL, reason="Invalid or missing token")
    return False


async def ingest_handler(
    websocket: WebSocket,
    config: EngineConfig,
    rule_engine: RuleEngine,
    broadcaster: EventBroadcaster | None = None,
) -> None:
    await websocket.accept()

    if not await verify_token(websocket, config):
        return

    client = websocket.client
    logger.info("Exporter connected: %s", client)

    try:
        while True:
            data = await websocket.receive_json()
            try:
                raw_log = RawLog(**data)
                event = parse(raw_log)

                if event is None:
                    logger.debug(
                        "[%s] Unparseable: %s", raw_log.exporter_id, raw_log.line[:80]
                    )
                    continue

                alerts = rule_engine.evaluate(event)

                if alerts:
                    for alert in alerts:
                        logger.warning(
                            "[ALERT][%s] %s — %s",
                            alert.severity.upper(),
                            alert.rule_name,
                            alert.description,
                        )

                    # broadcast alerts to dashboard.
                    if broadcaster:
                        for alert in alerts:
                            await broadcaster.broadcast(
                                {"type": "alert", "data": alert.model_dump(mode="json")}
                            )
                elif event.decoded:
                    logger.info(
                        "[%s] %s → %s %s",
                        raw_log.exporter_id,
                        event.program,
                        event.decoded.get("action", ""),
                        {k: v for k, v in event.decoded.items() if k != "action"},
                    )

                # broadcast all events to dashboard.
                if broadcaster:
                    await broadcaster.broadcast(
                        {"type": "event", "data": event.model_dump(mode="json")}
                    )

            except Exception as exc:
                logger.warning("Malformed message from %s: %s", client, exc)
                await websocket.close(code=CLOSE_MALFORMED, reason="Malformed payload")
                return
    except WebSocketDisconnect:
        logger.info("Exporter disconnected: %s", client)
