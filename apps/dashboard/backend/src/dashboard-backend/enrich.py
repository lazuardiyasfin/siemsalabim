import logging
from pathlib import Path
import maxminddb

logger = logging.getLogger(__name__)


# Assuming there's the db in /src
DB_PATH = Path(__file__).resolve().parent / "GeoLite2-City.mmdb"
_reader = None


def get_reader():
    global _reader
    if _reader is None and DB_PATH.exists():
        try:
            _reader = maxminddb.open_database(str(DB_PATH))
        except Exception as exc:
            logger.error("Failed to load MaxMind database: %s", exc)
    return _reader


def enrich_geoip(event: dict) -> dict:
    """Extracts the IP from the event schema, finds coordinates, and appends them."""
    try:
        source_events = event.get("source_events", [])
        if not source_events:
            return event

        decoded = source_events[0].get("decoded", {})
        src_ip = decoded.get("src_ip")

        if src_ip:
            reader = get_reader()
            if reader:
                try:
                    record = reader.get(src_ip)
                    if record and "location" in record:
                        loc = record["location"]
                        event["lat"] = loc.get("latitude")
                        event["lon"] = loc.get("longitude")
                        return event
                except ValueError:
                    pass

            # Fallback coordinates on Jakarta
            event["lat"] = -6.2088
            event["lon"] = 106.8456
    except Exception as exc:
        logger.error("GeoIP processing error: %s", exc)

    return event


def close_geoip_reader():
    global _reader
    if _reader is not None:
        _reader.close()
        _reader = None
