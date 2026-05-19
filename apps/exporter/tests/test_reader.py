from pathlib import Path

from src.reader import read_new_lines
from src.state import StateManager

class TestReadNewLines:
    def test_reads_all_lines_from_start(self, tmp_path: Path) -> None:
        """First read returns all complete lines."""
        log_file = tmp_path / "test.log"
        log_file.write_text("line one\nline two\nline three\n")
        sm = StateManager(tmp_path / "state.json")

        lines = read_new_lines(str(log_file), sm)

        assert lines == ["line one", "line two", "line three"]

    def test_incremental_read(self, tmp_path: Path) -> None:
        """Second read only returns new lines."""
        log_file = tmp_path / "test.log"
        log_file.write_text("first\n")
        sm = StateManager(tmp_path / "state.json")

        lines1 = read_new_lines(str(log_file), sm)
        assert lines1 == ["first"]

        # Append more data.
        with open(log_file, "a") as f:
            f.write("second\nthird\n")

        lines2 = read_new_lines(str(log_file), sm)
        assert lines2 == ["second", "third"]

    def test_skips_partial_line(self, tmp_path: Path) -> None:
        """Incomplete trailing line (no newline) is not returned."""
        log_file = tmp_path / "test.log"
        log_file.write_text("complete\npartial")
        sm = StateManager(tmp_path / "state.json")

        lines = read_new_lines(str(log_file), sm)

        assert lines == ["complete"]

    def test_partial_line_read_on_next_cycle(self, tmp_path: Path) -> None:
        """Partial line becomes available once newline is appended."""
        log_file = tmp_path / "test.log"
        log_file.write_text("complete\npartial")
        sm = StateManager(tmp_path / "state.json")

        read_new_lines(str(log_file), sm)

        with open(log_file, "a") as f:
            f.write(" now done\n")

        lines = read_new_lines(str(log_file), sm)
        assert lines == ["partial now done"]

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """Empty file returns no lines."""
        log_file = tmp_path / "test.log"
        log_file.write_text("")
        sm = StateManager(tmp_path / "state.json")

        assert read_new_lines(str(log_file), sm) == []

    def test_no_new_data_returns_empty(self, tmp_path: Path) -> None:
        """Reading again with no new data returns empty list."""
        log_file = tmp_path / "test.log"
        log_file.write_text("hello\n")
        sm = StateManager(tmp_path / "state.json")

        read_new_lines(str(log_file), sm)
        lines = read_new_lines(str(log_file), sm)

        assert lines == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Non-existent file returns empty list without raising."""
        sm = StateManager(tmp_path / "state.json")

        lines = read_new_lines("/tmp/does_not_exist_12345.log", sm)

        assert lines == []

    def test_truncated_file_resets(self, tmp_path: Path) -> None:
        """If file is smaller than offset, reset and re-read."""
        log_file = tmp_path / "test.log"
        log_file.write_text("a long line of content here\n")
        sm = StateManager(tmp_path / "state.json")

        read_new_lines(str(log_file), sm)

        log_file.write_text("short\n")

        lines = read_new_lines(str(log_file), sm)
        assert lines == ["short"]

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        """Blank lines are filtered out."""
        log_file = tmp_path / "test.log"
        log_file.write_text("line one\n\n\nline two\n")
        sm = StateManager(tmp_path / "state.json")

        lines = read_new_lines(str(log_file), sm)

        assert lines == ["line one", "line two"]