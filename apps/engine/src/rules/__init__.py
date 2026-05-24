import logging
from pathlib import Path

from ..models import Event
from .loader import load_rules_from_dir
from .matcher import RuleMatcher
from .models import Alert

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, rules_dir: Path) -> None:
        self._rules_dir = rules_dir
        self._matcher = self._load()

    def evaluate(self, event: Event) -> list[Alert]:
        """Evaluate an event against all loaded rules."""
        return self._matcher.evaluate(event)

    def reload(self) -> int:
        """Reload rules from disk. Returns new rule count."""
        self._matcher = self._load()
        return self._matcher.rule_count

    def _load(self) -> RuleMatcher:
        """Load rules and create a new matcher."""
        rules = load_rules_from_dir(self._rules_dir)
        logger.info("Rule engine loaded %d rule(s).", len(rules))
        return RuleMatcher(rules)

    @property
    def rule_count(self) -> int:
        """Number of loaded rules."""
        return self._matcher.rule_count
