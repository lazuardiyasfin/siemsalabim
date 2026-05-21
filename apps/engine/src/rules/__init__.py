import logging
from pathlib import Path

from ..models import Event
from .loader import load_rules_from_dir
from .matcher import RuleMatcher
from .models import Alert

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, rules_dir: Path) -> None:
        rules = load_rules_from_dir(rules_dir)
        self._matcher = RuleMatcher(rules)
        logger.info(
            "Rule engine initialized with %d rule(s).", self._matcher.rule_count
        )

    def evaluate(self, event: Event) -> list[Alert]:
        return self._matcher.evaluate(event)
