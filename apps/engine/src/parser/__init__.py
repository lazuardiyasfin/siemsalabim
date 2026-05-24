import logging
from pathlib import Path

from ..models import Event, RawLog
from .decoders import decode, init_decoders
from .predecoder import predecode

logger = logging.getLogger(__name__)


def init_parser(decoders_dir: Path) -> int:
    """Initialize the parser by loading decoder definitions."""
    count = init_decoders(decoders_dir)
    logger.info("Parser initialized with %d decoder(s).", count)
    return count


def parse(raw: RawLog) -> Event | None:
    """Parse a raw log into a structured Event."""
    pre = predecode(raw.line, source_path=raw.path)
    if pre is None:
        logger.debug("Could not predecode: %.120s", raw.line)
        return None

    decoded = decode(pre)

    return Event(
        timestamp=pre.timestamp,
        hostname=pre.hostname,
        program=pre.program,
        pid=pre.pid,
        log_format=pre.log_format,
        message=pre.message,
        decoded=decoded,
        exporter_id=raw.exporter_id,
        source_host=raw.host,
        source_path=raw.path,
    )
