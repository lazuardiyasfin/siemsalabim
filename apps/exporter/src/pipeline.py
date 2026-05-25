import asyncio
import logging
import os
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
    """Main exporter pipeline."""

    def __init__(self, config: ExporterConfig) -> None:
        self._config = config
        self._hostname = socket.gethostname()
        self._state = StateManager(config.state_file_path)
        self._ws = WebSocketClient(
            config.ingest_url,
            config.ingest_token,
            command_callback=self._handle_command,
        )
        self._event_queue: asyncio.Queue[str] = asyncio.Queue()
        self._watcher: LogWatcher | None = None
        self._extra_paths: list[str] = []

    async def run(self) -> None:
        """Start all components and block until cancelled."""
        self._state.load()
        self._extra_paths = self._state.load_extra_paths()

        loop = asyncio.get_running_loop()
        watch_paths = self._config.watch_paths_list + self._extra_paths
        self._watcher = LogWatcher(watch_paths, self._event_queue, loop)
        self._watcher.start()

        ws_task = asyncio.create_task(self._ws.start(), name="ws-client")
        process_task = asyncio.create_task(self._process_loop(), name="process-loop")
        save_task = asyncio.create_task(self._save_loop(), name="state-saver")

        logger.info(
            "Pipeline started — exporter_id=%s, watching %d path(s)"
            " (%d from config, %d extra).",
            self._config.exporter_id,
            len(watch_paths),
            len(self._config.watch_paths_list),
            len(self._extra_paths),
        )

        try:
            await asyncio.gather(ws_task, process_task, save_task)
        except asyncio.CancelledError:
            logger.info("Pipeline shutting down...")
            raise
        finally:
            self._watcher.stop()
            self._ws.stop()
            ws_task.cancel()
            process_task.cancel()
            save_task.cancel()
            self._state.save()
            logger.info("Pipeline stopped, final state saved.")

    def _handle_command(self, command: dict[str, object]) -> None:
        """Handle an incoming command from the engine."""
        cmd_type = command.get("type", "")

        if cmd_type == "add_path":
            path = str(command.get("path", ""))
            self._add_watch_path(path)
        else:
            logger.warning("Unknown command type: %s", cmd_type)

    def _add_watch_path(self, path: str) -> None:
        """Add a new log file path to watch at runtime and persist."""
        if not path:
            logger.warning("Empty path in add_path command, ignoring.")
            return

        if not os.path.exists(path):
            logger.warning("Path does not exist: %s", path)
            return

        if path in self._extra_paths:
            logger.info("Path already watched: %s", path)
            return

        if self._watcher is not None:
            self._watcher.add_path(path)

        self._extra_paths.append(path)
        self._state.save_extra_paths(self._extra_paths)
        logger.info("Added and persisted new watch path: %s", path)

    async def _process_loop(self) -> None:
        """Consume file-change events and ship new lines."""
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
        """Periodically flush state to disk."""
        while True:
            await asyncio.sleep(STATE_SAVE_INTERVAL)
            self._state.save()
