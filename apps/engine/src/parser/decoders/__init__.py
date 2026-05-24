import logging
import re
from pathlib import Path

from ...models import PreDecodedLog
from .loader import DecoderEntry, load_decoders_from_dir

logger = logging.getLogger(__name__)

_decoders: list[DecoderEntry] = []


def init_decoders(decoders_dir: Path) -> int:
    """Load decoders from YAML files. Returns count loaded."""
    global _decoders
    _decoders = load_decoders_from_dir(decoders_dir)
    return len(_decoders)


def reload_decoders(decoders_dir: Path) -> int:
    """Reload decoders from disk. Returns new count."""
    return init_decoders(decoders_dir)


def decode(pre: PreDecodedLog) -> dict[str, str | int | None]:
    """Run matching decoders against a pre-decoded log entry."""
    for entry in _decoders:
        if not _matches_filter(entry, pre):
            continue

        match = entry.pattern.search(pre.message)
        if match is None:
            continue

        return _build_result(entry, match)

    return {}


def _matches_filter(entry: DecoderEntry, pre: PreDecodedLog) -> bool:
    """Check if a decoder entry applies to this pre-decoded log."""
    if entry.program and entry.program.lower() != pre.program.lower():
        return False
    if entry.log_format and entry.log_format != pre.log_format.value:
        return False
    return True


def _build_result(
    entry: DecoderEntry, match: re.Match[str]
) -> dict[str, str | int | None]:
    """Build decoded fields dict from regex match + static fields."""

    result: dict[str, str | int | None] = {}

    for key, val in entry.static_fields.items():
        result[key] = val

    for key, val in match.groupdict().items():
        if val is None:
            result[key] = None
        elif key in entry.int_fields:
            result[key] = int(val)
        elif key in entry.dash_as_null and val == "-":
            result[key] = None
        else:
            result[key] = val

    if "pam_action" in result:
        pam_action = result.pop("pam_action")
        result["action"] = f"session_{pam_action}"

    return result
