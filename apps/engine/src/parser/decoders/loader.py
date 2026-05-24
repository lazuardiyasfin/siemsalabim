import logging
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DecoderEntry:
    """A single compiled decoder pattern."""

    id: str
    program: str
    log_format: str
    pattern: re.Pattern[str]
    static_fields: dict[str, str | None]
    int_fields: list[str]
    dash_as_null: list[str]


def load_decoders_from_file(path: Path) -> list[DecoderEntry]:
    """Load decoder entries from a single YAML file."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("Failed to load decoders from %s: %s", path, exc)
        return []

    if not isinstance(data, dict) or "decoders" not in data:
        logger.warning("No 'decoders' key found in %s.", path)
        return []

    entries: list[DecoderEntry] = []
    for item in data["decoders"]:
        try:
            entry = DecoderEntry(
                id=item["id"],
                program=item.get("program", ""),
                log_format=item.get("log_format", ""),
                pattern=re.compile(item["pattern"]),
                static_fields=item.get("fields", {}),
                int_fields=item.get("int_fields", []),
                dash_as_null=item.get("dash_as_null", []),
            )
            entries.append(entry)
            logger.debug("Loaded decoder '%s' from %s.", entry.id, path)
        except (KeyError, re.error) as exc:
            logger.warning("Invalid decoder in %s: %s", path, exc)

    return entries


def load_decoders_from_dir(directory: Path) -> list[DecoderEntry]:
    """Load all decoders from YAML files in a directory."""
    entries: list[DecoderEntry] = []

    if not directory.is_dir():
        logger.warning("Decoders directory not found: %s", directory)
        return entries

    for path in sorted(directory.glob("*.y*ml")):
        loaded = load_decoders_from_file(path)
        entries.extend(loaded)

    logger.info("Loaded %d decoder(s) from %s.", len(entries), directory)
    return entries
