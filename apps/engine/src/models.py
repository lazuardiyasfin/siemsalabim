from datetime import datetime

from pydantic import BaseModel, Field


class RawLog(BaseModel):
    exporter_id: str = Field(description="Unique identifier of the exporter instance.")
    host: str = Field(description="Hostname of the machine where the log originated.")
    path: str = Field(description="Absolute path of the log file.")
    line: str = Field(description="The raw log line content.")
    received_at: datetime = Field(
        description="UTC timestamp when the exporter read this line."
    )