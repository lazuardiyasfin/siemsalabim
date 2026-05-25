import asyncio
import time
from pathlib import Path
from unittest.mock import MagicMock

from src.watcher import LogWatcher, _LogFileHandler


class TestLogFileHandler:
    """Tests for the internal file handler."""

    def test_add_path_registers(self) -> None:
        """add_path adds to the watched set."""
        loop = MagicMock()
        queue: asyncio.Queue[str] = asyncio.Queue()
        handler = _LogFileHandler(set(), queue, loop)

        handler.add_path("/tmp/new.log")

        assert "/tmp/new.log" in handler._watched or any(
            "/tmp/new.log" in p or "new.log" in p for p in handler._watched
        )


class TestLogWatcher:
    """Tests for LogWatcher."""

    def test_start_and_stop(self, tmp_path: Path) -> None:
        """Watcher starts and stops without error."""
        log_file = tmp_path / "test.log"
        log_file.write_text("init\n")
        loop = asyncio.new_event_loop()
        queue: asyncio.Queue[str] = asyncio.Queue()

        watcher = LogWatcher([str(log_file)], queue, loop)
        watcher.start()
        time.sleep(0.1)
        watcher.stop()
        loop.close()

    def test_add_path_at_runtime(self, tmp_path: Path) -> None:
        """add_path adds new file to watcher without restart."""
        log_file = tmp_path / "test.log"
        log_file.write_text("init\n")
        new_file = tmp_path / "new.log"
        new_file.write_text("new\n")
        loop = asyncio.new_event_loop()
        queue: asyncio.Queue[str] = asyncio.Queue()

        watcher = LogWatcher([str(log_file)], queue, loop)
        watcher.start()

        watcher.add_path(str(new_file))
        assert str(new_file) in watcher._watch_paths

        watcher.stop()
        loop.close()

    def test_stop_without_start(self) -> None:
        """Stopping a watcher that was never started does not crash."""
        loop = asyncio.new_event_loop()
        queue: asyncio.Queue[str] = asyncio.Queue()
        watcher = LogWatcher([], queue, loop)
        watcher.stop()
        loop.close()

    def test_duplicate_directory_not_scheduled_twice(self, tmp_path: Path) -> None:
        """Same parent directory is only scheduled once."""
        file1 = tmp_path / "a.log"
        file2 = tmp_path / "b.log"
        file1.write_text("a\n")
        file2.write_text("b\n")
        loop = asyncio.new_event_loop()
        queue: asyncio.Queue[str] = asyncio.Queue()

        watcher = LogWatcher([str(file1), str(file2)], queue, loop)
        watcher.start()

        assert len(watcher._scheduled_dirs) == 1

        watcher.stop()
        loop.close()
