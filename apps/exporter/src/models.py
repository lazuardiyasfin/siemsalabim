from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RawLog(BaseModel):
    exporter_id: str = Field(description="Unique identifier of the exporter instance.")
    host: str = Field(description="Hostname of the machine where the log originated.")
    path: str = Field(description="Absolute path of the log file.")
    line: str = Field(description="The raw log line content.")
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp when the exporter read this line.",
    )
