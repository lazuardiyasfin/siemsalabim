import logging
from pathlib import Path

import yaml

from .models import Rule

logger = logging.getLogger(__name__)


def load_rules_from_file(path: Path) -> list[Rule]:

    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("Failed to load rules from %s: %s", path, exc)
        return []

    if not isinstance(data, dict) or "rules" not in data:
        logger.warning("No 'rules' key found in %s.", path)
        return []

    rules: list[Rule] = []
    for entry in data["rules"]:
        try:
            rule = Rule(**entry)
            rules.append(rule)
            logger.debug("Loaded rule '%s' from %s.", rule.id, path)
        except Exception as exc:
            logger.warning("Invalid rule in %s: %s", path, exc)

    return rules


def load_rules_from_dir(directory: Path) -> list[Rule]:

    rules: list[Rule] = []

    if not directory.is_dir():
        logger.warning("Rules directory not found: %s", directory)
        return rules

    for path in sorted(directory.glob("*.y*ml")):
        loaded = load_rules_from_file(path)
        rules.extend(loaded)

    logger.info("Loaded %d rule(s) from %s.", len(rules), directory)
    return rules
