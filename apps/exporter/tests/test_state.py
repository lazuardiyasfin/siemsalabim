import json
from pathlib import Path

from src.state import StateManager

class TestStateManager:
    def test_new_file_returns_zero_offset(self, tmp_path: Path) -> None:
        """First access to an unknown file returns offset 0."""
        sm = StateManager(tmp_path / "state.json")
        log_file = tmp_path / "test.log"
        log_file.write_text("hello\n")

        assert sm.get_offset(str(log_file)) == 0

    def test_set_and_get_offset(self, tmp_path: Path) -> None:
        """Setting an offset is reflected on next get."""
        sm = StateManager(tmp_path / "state.json")
        log_file = tmp_path / "test.log"
        log_file.write_text("hello\nworld\n")

        sm.set_offset(str(log_file), 42)

        assert sm.get_offset(str(log_file)) == 42

    def test_save_and_load(self, tmp_path: Path) -> None:
        """State survives save + load cycle."""
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
        """Loading from non-existent file doesn't crash."""
        sm = StateManager(tmp_path / "nope.json")
        sm.load()

    def test_load_corrupt_file_starts_fresh(self, tmp_path: Path) -> None:
        """Corrupt state file is handled gracefully."""
        state_path = tmp_path / "state.json"
        state_path.write_text("NOT JSON {{{", encoding="utf-8")

        sm = StateManager(state_path)
        sm.load()

        log_file = tmp_path / "test.log"
        log_file.write_text("line\n")
        assert sm.get_offset(str(log_file)) == 0

    def test_rotation_resets_offset(self, tmp_path: Path) -> None:
        """When inode changes (simulated rotation), offset resets to 0."""
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
        """Save creates intermediate directories if needed."""
        state_path = tmp_path / "deep" / "nested" / "state.json"
        sm = StateManager(state_path)
        sm.set_offset("/tmp/some.log", 10)
        sm.save()

        assert state_path.exists()
        data = json.loads(state_path.read_text())
        assert data["/tmp/some.log"]["offset"] == 10