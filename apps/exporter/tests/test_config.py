import pytest
from pydantic import ValidationError

from src.config import ExporterConfig


class TestExporterConfig:
    def test_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads all required fields from SIEM_ prefixed env vars."""
        monkeypatch.setenv("SIEM_INGEST_URL", "ws://localhost:8000/ws/ingest")
        monkeypatch.setenv("SIEM_INGEST_TOKEN", "testtoken")
        monkeypatch.setenv("SIEM_EXPORTER_ID", "test-node")
        monkeypatch.setenv("SIEM_WATCH_PATHS", "/var/log/auth.log")

        config = ExporterConfig()

        assert config.ingest_url == "ws://localhost:8000/ws/ingest"
        assert config.ingest_token == "testtoken"
        assert config.exporter_id == "test-node"
        assert config.watch_paths == "/var/log/auth.log"

    def test_watch_paths_list_single(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Single path is parsed into a one-element list."""
        monkeypatch.setenv("SIEM_INGEST_URL", "ws://localhost:8000/ws/ingest")
        monkeypatch.setenv("SIEM_INGEST_TOKEN", "t")
        monkeypatch.setenv("SIEM_EXPORTER_ID", "n")
        monkeypatch.setenv("SIEM_WATCH_PATHS", "/var/log/syslog")

        config = ExporterConfig()

        assert config.watch_paths_list == ["/var/log/syslog"]

    def test_watch_paths_list_multiple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Comma-separated paths are split correctly."""
        monkeypatch.setenv("SIEM_INGEST_URL", "ws://localhost:8000/ws/ingest")
        monkeypatch.setenv("SIEM_INGEST_TOKEN", "t")
        monkeypatch.setenv("SIEM_EXPORTER_ID", "n")
        monkeypatch.setenv(
            "SIEM_WATCH_PATHS", "/var/log/auth.log, /var/log/nginx/access.log"
        )

        config = ExporterConfig()

        assert config.watch_paths_list == [
            "/var/log/auth.log",
            "/var/log/nginx/access.log",
        ]

    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default values are applied for optional fields."""
        monkeypatch.setenv("SIEM_INGEST_URL", "ws://localhost:8000/ws/ingest")
        monkeypatch.setenv("SIEM_INGEST_TOKEN", "t")
        monkeypatch.setenv("SIEM_EXPORTER_ID", "n")
        monkeypatch.setenv("SIEM_WATCH_PATHS", "/tmp/test.log")

        config = ExporterConfig()

        assert config.log_level == "INFO"
        assert str(config.state_file_path) == "/var/lib/exporter/state.json"

    def test_missing_required_field_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing required env var raises ValidationError."""
        monkeypatch.delenv("SIEM_INGEST_URL", raising=False)
        monkeypatch.delenv("SIEM_INGEST_TOKEN", raising=False)
        monkeypatch.delenv("SIEM_EXPORTER_ID", raising=False)
        monkeypatch.delenv("SIEM_WATCH_PATHS", raising=False)

        with pytest.raises(ValidationError):
            ExporterConfig()
