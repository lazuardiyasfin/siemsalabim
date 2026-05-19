import asyncio
import logging
import socket
from datetime import datetime, timezone

from .config import ExporterConfig
from .models import RawLog
from .reader import read_new_lines
from .state import StateManager
from .watcher import LogWatcher
from .ws_client import WebSocketClient

logger = logging.getLogger(__name__)

STATE_SAVE_INTERVAL: float = 10.0


class Pipeline:
    def __init__(self, config: ExporterConfig) -> None:
        self._config = config
        self._hostname = socket.gethostname()
        self._state = StateManager(config.state_file_path)
        self._ws = WebSocketClient(config.ingest_url, config.ingest_token)
        self._event_queue: asyncio.Queue[str] = asyncio.Queue()

    async def run(self) -> None:
        self._state.load()

        loop = asyncio.get_running_loop()
        watch_paths = self._config.watch_paths_list
        watcher = LogWatcher(watch_paths, self._event_queue, loop)
        watcher.start()

        ws_task = asyncio.create_task(self._ws.start(), name="ws-client")
        process_task = asyncio.create_task(self._process_loop(), name="process-loop")
        save_task = asyncio.create_task(self._save_loop(), name="state-saver")

        logger.info(
            "Pipeline started — exporter_id=%s, watching %d path(s).",
            self._config.exporter_id,
            len(watch_paths),
        )

        try:
            await asyncio.gather(ws_task, process_task, save_task)
        except asyncio.CancelledError:
            logger.info("Pipeline shutting down...")
        finally:
            watcher.stop()
            self._ws.stop()
            ws_task.cancel()
            process_task.cancel()
            save_task.cancel()
            self._state.save()
            logger.info("Pipeline stopped, final state saved.")

    async def _process_loop(self) -> None:
        while True:
            file_path = await self._event_queue.get()
            lines = read_new_lines(file_path, self._state)

            for line in lines:
                raw_log = RawLog(
                    exporter_id=self._config.exporter_id,
                    host=self._hostname,
                    path=file_path,
                    line=line,
                    received_at=datetime.now(tz=timezone.utc),
                )
                payload = raw_log.model_dump_json()
                self._ws.enqueue(payload)

            self._event_queue.task_done()

    async def _save_loop(self) -> None:
        while True:
            await asyncio.sleep(STATE_SAVE_INTERVAL)
            self._state.save()