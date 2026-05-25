from pydantic import Field
from pydantic_settings import BaseSettings


class EngineConfig(BaseSettings):
    model_config = {"env_prefix": "SIEM_"}

    ingest_token: str = Field(
        description="Bearer token to validate incoming exporter connections.",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level.",
    )
    discord_webhook_url: str | None = Field(
        default=None,
        description="Discord Webhook URL for alerting.",
    )
