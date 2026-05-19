from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class ExporterConfig(BaseSettings):
    model_config = {"env_prefix": "SIEM_"}

    ingest_url: str = Field(
        description="WebSocket URL of the engine ingest endpoint.",
        examples=["wss://siemsalabim.duckdns.org/ws/ingest"],
    )
    ingest_token: str = Field(
        description="Bearer token for authenticating with the ingest endpoint.",
    )
    exporter_id: str = Field(
        description="Unique identifier for this exporter instance.",
        examples=["node-target-prod-01"],
    )
    watch_paths: str = Field(
        description="Comma-separated list of log file paths to watch.",
        examples=["/var/log/auth.log,/var/log/nginx/access.log"],
    )
    state_file_path: Path = Field(
        default=Path("/var/lib/exporter/state.json"),
        description="Path to the JSON file used for offset persistence.",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level.",
    )

    @property
    def watch_paths_list(self) -> list[str]:
        """Parse comma-separated watch paths into a list."""
        return [p.strip() for p in self.watch_paths.split(",") if p.strip()]
