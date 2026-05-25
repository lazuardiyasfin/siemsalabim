import logging
import asyncio
import json
import urllib.request

from fastapi import WebSocket, WebSocketDisconnect

from .broadcaster import EventBroadcaster
from .config import EngineConfig
from .database import store_events_and_alerts
from .exporter_manager import ExporterManager
from .models import RawLog
from .parser import parse
from .rules import RuleEngine
from .rules.models import Alert

logger = logging.getLogger(__name__)

CLOSE_AUTH_FAIL = 1008
CLOSE_MALFORMED = 1003


def _send_discord_sync(url: str, payload: dict) -> None:
    """Sync function to push webhook using stdlib."""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SIEM-Engine/1.0",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
        logger.info("Successfully fired Discord webhook!")
    except Exception as e:
        logger.error("Discord webhook failed: %s", e)


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
    config: EngineConfig,
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
        for alert in alerts:
            alert_data = alert.model_dump(mode="json")
            notifications = alert_data.get("notifications", {})
            logger.info(
                f"DEBUG ALERT: Rule={alert.rule_name} | Notifications={notifications} | URL={config.discord_webhook_url}"
            )
            if notifications.get("discord") and config.discord_webhook_url:
                source = (
                    event.decoded.get("src_ip")
                    or event.decoded.get("client_ip")
                    or "Unknown Host"
                )
                emoji = (
                    "🔴"
                    if alert.severity == "critical"
                    else "🟠"
                    if alert.severity == "high"
                    else "🟡"
                )

                payload = {
                    "content": f"{emoji} **{alert.severity.upper()}** - {alert.rule_name} by `{source}`\n> {alert.description}"
                }

                asyncio.create_task(
                    asyncio.to_thread(
                        _send_discord_sync, config.discord_webhook_url, payload
                    )
                )
        if broadcaster:
            for alert in alerts:
                await broadcaster.broadcast(
                    {"type": "alert", "data": alert.model_dump(mode="json")}
                )
    elif event.decoded:
        _log_event(raw_log, event.program, event.decoded)

    try:
        await store_events_and_alerts(event, alerts)
    except Exception as db_err:
        logger.error("Failed to write data to database: %s", db_err)

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

                await _process_message(data, rule_engine, broadcaster, config)
            except Exception as exc:
                logger.warning("Malformed message from %s: %s", client, exc)
                await websocket.close(code=CLOSE_MALFORMED, reason="Malformed payload")
                return
    except WebSocketDisconnect:
        logger.info("Exporter disconnected: %s", client)
    finally:
        if exporter_id and exporter_mgr:
            exporter_mgr.unregister(exporter_id)
