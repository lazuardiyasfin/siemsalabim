import asyncio
import logging
import time

logger = logging.getLogger(__name__)


async def broadcast_to_frontends(state, event: dict) -> None:
    """Broadcast JSON payloads to all connected WebSocket clients safely."""
    disconnected = set()
    for websocket in state.connected_frontends:
        try:
            await websocket.send_json(event)
        except Exception as exc:
            logger.warning("Failed to send event to frontend: %s", exc)
            disconnected.add(websocket)

    for websocket in disconnected:
        state.connected_frontends.discard(websocket)


async def eps_broadcast_worker(state) -> None:
    """Calculate and broadcast EPS to frontends every 1 second."""
    while True:
        try:
            await asyncio.sleep(1)
            current_eps = state.event_counter
            state.event_counter = 0  # Atomic reset for the next interval

            payload = {"type": "EPS_UPDATE", "value": current_eps}
            await broadcast_to_frontends(state, payload)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Error in EPS broadcast worker: %s", exc)


async def exporter_monitor_worker(state, timeout_seconds: int = 30) -> None:
    """Monitor the exporter registry and broadcast changes in active worker counts."""
    while True:
        try:
            await asyncio.sleep(5)  # Verify status every 5 seconds
            now = time.time()

            # Identify active exporters within the valid window
            active_exporters = {
                exp_id: last_seen
                for exp_id, last_seen in state.exporter_registry.items()
                if now - last_seen < timeout_seconds
            }

            current_count = len(active_exporters)
            state.exporter_registry = active_exporters  # Prune inactive entries

            # Broadcast updates only when changes occur
            if current_count != state.active_exporters_count:
                state.active_exporters_count = current_count
                payload = {"type": "EXPORTER_STATUS", "count": current_count}
                await broadcast_to_frontends(state, payload)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Error in exporter monitor worker: %s", exc)
