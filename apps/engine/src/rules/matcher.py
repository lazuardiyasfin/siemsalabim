"""Rule matcher — Supports two types of rules:

1. Single-event rules: all conditions must match the current event.
   Fires an alert immediately.

2. Frequency rules: conditions must match, AND the event count
   within a time window (grouped by a field) must reach a threshold.
   Example: 5 failed SSH logins from the same IP within 2 minutes.
"""

import logging
import time
from collections import defaultdict

from ..models import Event
from .models import Alert, FrequencyConfig, Rule, RuleCondition

logger = logging.getLogger(__name__)


class _FrequencyTracker:
    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def record_and_check(
        self,
        rule_id: str,
        group_value: str,
        freq: FrequencyConfig,
    ) -> int:
        now = time.time()
        cutoff = now - freq.window_seconds
        bucket = self._buckets[rule_id][group_value]

        self._buckets[rule_id][group_value] = [t for t in bucket if t > cutoff]
        self._buckets[rule_id][group_value].append(now)

        return len(self._buckets[rule_id][group_value])

    def clear(self, rule_id: str, group_value: str) -> None:
        self._buckets[rule_id][group_value] = []


class RuleMatcher:
    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules
        self._tracker = _FrequencyTracker()

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def evaluate(self, event: Event) -> list[Alert]:
        alerts: list[Alert] = []

        for rule in self._rules:
            if not self._matches_program(rule, event):
                continue

            if not self._matches_conditions(rule.conditions, event):
                continue

            if rule.frequency is not None:
                alert = self._check_frequency(rule, event)
                if alert is not None:
                    alerts.append(alert)
            else:
                alerts.append(self._make_alert(rule, event))

        return alerts

    def _matches_program(self, rule: Rule, event: Event) -> bool:
        if not rule.program:
            return True
        return rule.program.lower() == event.program.lower()

    def _matches_conditions(
        self,
        conditions: list[RuleCondition],
        event: Event,
    ) -> bool:
        for cond in conditions:
            value = self._get_field(event, cond.field)
            if value is None:
                return False
            if not self._value_matches(value, cond.value):
                return False
        return True

    def _check_frequency(self, rule: Rule, event: Event) -> Alert | None:
        freq = rule.frequency
        if freq is None:
            return None

        group_value = str(self._get_field(event, freq.group_by) or "unknown")
        count = self._tracker.record_and_check(rule.id, group_value, freq)

        if count >= freq.count:
            self._tracker.clear(rule.id, group_value)
            return self._make_alert(rule, event, event_count=count)

        return None

    def _make_alert(
        self,
        rule: Rule,
        event: Event,
        event_count: int = 1,
    ) -> Alert:
        description = rule.description
        if event.decoded:
            for key, val in event.decoded.items():
                description = description.replace(f"{{{key}}}", str(val or ""))

        return Alert(
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            description=description,
            event_count=event_count,
            source_events=[event.model_dump()],
            notifications=rule.notifications,
        )

    @staticmethod
    def _get_field(event: Event, field_path: str) -> object:
        parts = field_path.split(".")
        current: object = event

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

        return current

    @staticmethod
    def _value_matches(actual: object, expected: str | list[str]) -> bool:
        actual_str = str(actual)
        if isinstance(expected, list):
            return actual_str in expected
        return actual_str == expected
