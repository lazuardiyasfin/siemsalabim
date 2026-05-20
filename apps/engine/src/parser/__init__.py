import logging

from ..models import Event, RawLog
from .decoders import decode
from .predecoder import predecode

logger = logging.getLogger(__name__)


def parse(raw: RawLog) -> Event | None:
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
