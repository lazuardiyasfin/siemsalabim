from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleCondition(BaseModel):
    field: str = Field(
        description="Dot-path to the field in Event (e.g. 'decoded.action')."
    )
    value: str | list[str] = Field(
        description="Expected value or list of values (any match).",
    )


class FrequencyConfig(BaseModel):
    count: int = Field(description="Number of events to trigger alert.")
    window_seconds: int = Field(description="Time window in seconds.")
    group_by: str = Field(
        default="decoded.src_ip",
        description="Field to group events by (e.g. per source IP).",
    )


class Rule(BaseModel):
    id: str = Field(description="Unique rule identifier.")
    name: str = Field(description="Human-readable rule name.")
    severity: Severity = Field(description="Alert severity when rule fires.")
    description: str = Field(default="", description="Rule description template.")
    program: str = Field(
        default="",
        description="Filter: only apply to events from this program.",
    )
    conditions: list[RuleCondition] = Field(
        default_factory=list,
        description="All conditions must match (AND logic).",
    )
    frequency: FrequencyConfig | None = Field(
        default=None,
        description="If set, rule is frequency-based (requires N events in window).",
    )


class Alert(BaseModel):
    rule_id: str = Field(description="ID of the rule that fired.")
    rule_name: str = Field(description="Human-readable rule name.")
    severity: Severity = Field(description="Alert severity level.")
    description: str = Field(description="Description of what triggered the alert.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When the alert was generated.",
    )
    event_count: int = Field(
        default=1,
        description="Number of events that triggered this alert.",
    )
    source_events: list[dict[str, object]] = Field(
        default_factory=list,
        description="The event(s) that triggered the alert.",
    )
