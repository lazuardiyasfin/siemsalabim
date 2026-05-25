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
    """Watchdog handler that filters for watched paths and debounces."""

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

    def add_path(self, path: str) -> None:
        """Add a new path to the watched set at runtime."""
        real = os.path.realpath(path)
        self._watched.add(real)

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
    """Watches log files for changes and feeds an asyncio queue."""

    def __init__(
        self,
        watch_paths: list[str],
        queue: asyncio.Queue[str],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self._watch_paths = list(watch_paths)
        self._handler = _LogFileHandler(set(watch_paths), queue, loop)
        self._observer = Observer()
        self._scheduled_dirs: set[str] = set()
        self._scheduled = False

    def start(self) -> None:
        """Begin watching."""
        for p in self._watch_paths:
            self._schedule_dir(str(Path(p).parent))

        self._observer.start()
        self._scheduled = True
        logger.info("File watcher started for %d path(s).", len(self._watch_paths))

    def add_path(self, path: str) -> None:
        """Add a new log file path to watch at runtime."""
        self._watch_paths.append(path)
        self._handler.add_path(path)
        parent = str(Path(path).parent)
        self._schedule_dir(parent)
        logger.info("Added watch path: %s", path)

    def stop(self) -> None:
        """Stop the observer thread."""
        if self._scheduled:
            self._observer.stop()
            self._observer.join()
            self._scheduled = False
            logger.info("File watcher stopped.")

    def _schedule_dir(self, directory: str) -> None:
        """Schedule a directory for watching if not already scheduled."""
        if directory not in self._scheduled_dirs:
            self._observer.schedule(self._handler, directory, recursive=False)
            self._scheduled_dirs.add(directory)
            logger.info("Watching directory %s for changes.", directory)
