import json
from pathlib import Path

from src.state import StateManager


class TestStateManager:
    """Tests for StateManager offset tracking and persistence."""

    def test_new_file_returns_zero_offset(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "state.json")
        log_file = tmp_path / "test.log"
        log_file.write_text("hello\n")
        assert sm.get_offset(str(log_file)) == 0

    def test_set_and_get_offset(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "state.json")
        log_file = tmp_path / "test.log"
        log_file.write_text("hello\nworld\n")
        sm.set_offset(str(log_file), 42)
        assert sm.get_offset(str(log_file)) == 42

    def test_save_and_load(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        log_file = tmp_path / "test.log"
        log_file.write_text("data\n")
        sm1 = StateManager(state_path)
        sm1.set_offset(str(log_file), 100)
        sm1.save()
        sm2 = StateManager(state_path)
        sm2.load()
        assert sm2.get_offset(str(log_file)) == 100

    def test_load_missing_file_starts_fresh(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "nope.json")
        sm.load()

    def test_load_corrupt_file_starts_fresh(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state_path.write_text("NOT JSON {{{", encoding="utf-8")
        sm = StateManager(state_path)
        sm.load()
        log_file = tmp_path / "test.log"
        log_file.write_text("line\n")
        assert sm.get_offset(str(log_file)) == 0

    def test_rotation_resets_offset(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        log_file = tmp_path / "test.log"
        log_file.write_text("original content\n")
        sm = StateManager(state_path)
        sm.get_offset(str(log_file))
        sm.set_offset(str(log_file), 500)
        log_file.unlink()
        log_file.write_text("rotated content\n")
        offset = sm.get_offset(str(log_file))
        assert offset == 0

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        state_path = tmp_path / "deep" / "nested" / "state.json"
        sm = StateManager(state_path)
        sm.set_offset("/tmp/some.log", 10)
        sm.save()
        assert state_path.exists()
        data = json.loads(state_path.read_text())
        assert data["/tmp/some.log"]["offset"] == 10


class TestExtraPaths:
    """Tests for extra paths persistence."""

    def test_save_and_load_extra_paths(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "state.json")
        paths = ["/var/log/mysql/error.log", "/var/log/redis.log"]
        sm.save_extra_paths(paths)
        loaded = sm.load_extra_paths()
        assert loaded == paths

    def test_load_empty_returns_empty(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "state.json")
        assert sm.load_extra_paths() == []

    def test_load_corrupt_returns_empty(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "state.json")
        extra_path = tmp_path / "extra_paths.json"
        extra_path.write_text("NOT JSON", encoding="utf-8")
        assert sm.load_extra_paths() == []

    def test_extra_paths_file_location(self, tmp_path: Path) -> None:
        sm = StateManager(tmp_path / "state.json")
        sm.save_extra_paths(["/tmp/test.log"])
        extra_file = tmp_path / "extra_paths.json"
        assert extra_file.exists()
        data = json.loads(extra_file.read_text())
        assert data == ["/tmp/test.log"]
