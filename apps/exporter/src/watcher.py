import asyncio
import logging
import os
import time
from pathlib import Path

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

DEBOUNCE_SECONDS: float = 0.5


class _LogFileHandler(FileSystemEventHandler):
    def __init__(
        self,
        watched_paths: set[str],
        queue: asyncio.Queue[str],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__()
        self._watched = {os.path.realpath(p) for p in watched_paths}
        self._queue = queue
        self._loop = loop
        self._last_event: dict[str, float] = {}

    def on_modified(self, event: FileModifiedEvent) -> None: 
        if event.is_directory:
            return
        
        src = os.path.realpath(str(event.src_path))

        if src not in self._watched:
            return

        now = time.monotonic()
        last = self._last_event.get(src, 0.0)
        if now - last < DEBOUNCE_SECONDS:
            return

        self._last_event[src] = now
        self._loop.call_soon_threadsafe(self._queue.put_nowait, src)
        logger.debug("Queued modification event for %s.", src)


class LogWatcher:
    def __init__(
        self,
        watch_paths: list[str],
        queue: asyncio.Queue[str],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self._watch_paths = watch_paths
        self._handler = _LogFileHandler(set(watch_paths), queue, loop)
        self._observer = Observer()
        self._scheduled = False

    def start(self) -> None:
        directories: set[str] = set()
        for p in self._watch_paths:
            parent = str(Path(p).parent)
            directories.add(parent)

        for directory in directories:
            self._observer.schedule(self._handler, directory, recursive=False)
            logger.info("Watching directory %s for changes.", directory)

        self._observer.start()
        self._scheduled = True
        logger.info("File watcher started for %d path(s).", len(self._watch_paths))

    def stop(self) -> None:
        if self._scheduled:
            self._observer.stop()
            self._observer.join()
            self._scheduled = False
            logger.info("File watcher stopped.")