import re

_COMBINED_RE = re.compile(
    r"^(?P<client_ip>\S+)"
    r"\s+(?P<ident>\S+)"
    r"\s+(?P<auth_user>\S+)"
    r"\s+\[(?P<timestamp>[^\]]+)\]"
    r'\s+"(?P<method>[A-Z]+)\s+(?P<path>\S+)\s+(?P<protocol>[^"]*)"'
    r"\s+(?P<status>\d{3})"
    r"\s+(?P<bytes>\d+)"
    r'\s+"(?P<referer>[^"]*)"'
    r'\s+"(?P<user_agent>[^"]*)"'
)

_MALFORMED_RE = re.compile(
    r"^(?P<client_ip>\S+)"
    r"\s+\S+"
    r"\s+\S+"
    r"\s+\[(?P<timestamp>[^\]]+)\]"
    r'\s+"(?P<raw_request>[^"]*)"'
    r"\s+(?P<status>\d{3})"
    r"\s+(?P<bytes>\d+)"
)


def decode_nginx(message: str) -> dict[str, str | int | None]:
    match = _COMBINED_RE.match(message)
    if match:
        return {
            "client_ip": match.group("client_ip"),
            "method": match.group("method"),
            "path": match.group("path"),
            "protocol": match.group("protocol"),
            "status": int(match.group("status")),
            "bytes": int(match.group("bytes")),
            "referer": _clean_dash(match.group("referer")),
            "user_agent": _clean_dash(match.group("user_agent")),
        }

    match = _MALFORMED_RE.match(message)
    if match:
        return {
            "client_ip": match.group("client_ip"),
            "method": None,
            "path": None,
            "raw_request": match.group("raw_request"),
            "status": int(match.group("status")),
            "bytes": int(match.group("bytes")),
        }

    return {}


def _clean_dash(value: str) -> str | None:
    """Return None for nginx's ``-`` placeholder."""
    return None if value == "-" else value
