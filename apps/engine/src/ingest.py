import logging

from fastapi import WebSocket, WebSocketDisconnect

from .config import EngineConfig
from .models import RawLog

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


async def ingest_handler(websocket: WebSocket, config: EngineConfig) -> None:
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
                logger.info(
                    "[%s] %s:%s — %s",
                    raw_log.exporter_id,
                    raw_log.host,
                    raw_log.path,
                    raw_log.line[:120],
                )
            except Exception as exc:
                logger.warning("Malformed message from %s: %s", client, exc)
                await websocket.close(code=CLOSE_MALFORMED, reason="Malformed JSON")
                return
    except WebSocketDisconnect:
        logger.info("Exporter disconnected: %s", client)