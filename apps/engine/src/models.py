from datetime import datetime

from pydantic import BaseModel, Field

from enum import StrEnum


class RawLog(BaseModel):
    exporter_id: str = Field(description="Unique identifier of the exporter instance.")
    host: str = Field(description="Hostname of the machine where the log originated.")
    path: str = Field(description="Absolute path of the log file.")
    line: str = Field(description="The raw log line content.")
    received_at: datetime = Field(
        description="UTC timestamp when the exporter read this line."
    )


class LogFormat(StrEnum):
    """Detected log format."""

    SYSLOG = "syslog"
    NGINX_ACCESS = "nginx_access"
    UNKNOWN = "unknown"


class PreDecodedLog(BaseModel):
    timestamp: str = Field(description="Raw timestamp string from the log line.")
    hostname: str = Field(description="Hostname that produced the log.")
    program: str = Field(default="", description="Program name (e.g. sshd, nginx).")
    pid: int | None = Field(default=None, description="Process ID if available.")
    message: str = Field(description="Remaining message after common fields.")
    log_format: LogFormat = Field(description="Detected log format.")


class Event(BaseModel):
    timestamp: str = Field(description="Timestamp from the log line.")
    hostname: str = Field(description="Source hostname.")
    program: str = Field(description="Source program.")
    pid: int | None = Field(default=None, description="Process ID.")
    log_format: LogFormat = Field(description="Detected log format.")
    message: str = Field(description="Original message content.")
    decoded: dict[str, str | int | None] = Field(
        default_factory=dict,
        description="Program-specific decoded fields.",
    )

    exporter_id: str = Field(default="")
    source_host: str = Field(default="")
    source_path: str = Field(default="")
    notifications: dict[str, bool] = Field(default_factory=dict)
