from pathlib import Path
from unittest.mock import MagicMock

from src.pipeline import Pipeline


def _make_config(tmp_path: Path) -> MagicMock:
    """Create a mock ExporterConfig."""
    config = MagicMock()
    config.ingest_url = "ws://localhost:8000/ws/ingest"
    config.ingest_token = "testtoken"
    config.exporter_id = "test-node"
    config.watch_paths = "/tmp/test.log"
    config.watch_paths_list = ["/tmp/test.log"]
    config.state_file_path = tmp_path / "state.json"
    config.log_level = "INFO"
    return config


class TestPipelineCommand:
    """Tests for pipeline command handling."""

    def test_handle_add_path_command(self, tmp_path: Path) -> None:
        """add_path command adds path and persists."""
        config = _make_config(tmp_path)
        pipeline = Pipeline(config)
        pipeline._watcher = MagicMock()
        pipeline._extra_paths = []

        log_file = tmp_path / "new.log"
        log_file.write_text("test\n")

        pipeline._handle_command({"type": "add_path", "path": str(log_file)})

        assert str(log_file) in pipeline._extra_paths
        pipeline._watcher.add_path.assert_called_once_with(str(log_file))

    def test_handle_add_path_empty(self, tmp_path: Path) -> None:
        """Empty path is ignored."""
        config = _make_config(tmp_path)
        pipeline = Pipeline(config)
        pipeline._extra_paths = []

        pipeline._handle_command({"type": "add_path", "path": ""})

        assert pipeline._extra_paths == []

    def test_handle_add_path_nonexistent(self, tmp_path: Path) -> None:
        """Non-existent path is ignored."""
        config = _make_config(tmp_path)
        pipeline = Pipeline(config)
        pipeline._extra_paths = []

        pipeline._handle_command({"type": "add_path", "path": "/nonexistent/path.log"})

        assert pipeline._extra_paths == []

    def test_handle_add_path_duplicate(self, tmp_path: Path) -> None:
        """Duplicate path is not added twice."""
        config = _make_config(tmp_path)
        pipeline = Pipeline(config)
        pipeline._watcher = MagicMock()

        log_file = tmp_path / "dup.log"
        log_file.write_text("test\n")
        path_str = str(log_file)

        pipeline._extra_paths = [path_str]

        pipeline._handle_command({"type": "add_path", "path": path_str})

        assert pipeline._extra_paths.count(path_str) == 1

    def test_handle_unknown_command(self, tmp_path: Path) -> None:
        """Unknown command type is logged but does not crash."""
        config = _make_config(tmp_path)
        pipeline = Pipeline(config)

        pipeline._handle_command({"type": "unknown_cmd"})

    def test_add_path_persists_to_state(self, tmp_path: Path) -> None:
        """Added path is saved via state manager."""
        config = _make_config(tmp_path)
        pipeline = Pipeline(config)
        pipeline._watcher = MagicMock()
        pipeline._extra_paths = []

        log_file = tmp_path / "persist.log"
        log_file.write_text("data\n")

        pipeline._add_watch_path(str(log_file))

        extra_paths_file = tmp_path / "extra_paths.json"
        assert extra_paths_file.exists()
