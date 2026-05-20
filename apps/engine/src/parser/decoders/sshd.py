import re

_INVALID_USER_RE = re.compile(
    r"Invalid user (?P<user>\S+) from (?P<src_ip>\S+) port (?P<src_port>\d+)"
)

_ACCEPTED_RE = re.compile(
    r"Accepted (?P<method>\S+) for (?P<user>\S+) from (?P<src_ip>\S+)"
    r" port (?P<src_port>\d+)"
)

_FAILED_RE = re.compile(
    r"Failed (?P<method>\S+) for (?:invalid user )?(?P<user>\S+)"
    r" from (?P<src_ip>\S+) port (?P<src_port>\d+)"
)

_CONN_CLOSED_RE = re.compile(
    r"Connection closed by (?:invalid user )?(?P<user>\S+)?\s*(?P<src_ip>\S+)"
    r" port (?P<src_port>\d+)"
)

_DISCONNECTED_RE = re.compile(
    r"Disconnected from (?:invalid user )?(?P<user>\S+)"
    r" (?P<src_ip>\S+) port (?P<src_port>\d+)"
)

_CONN_RESET_RE = re.compile(
    r"Connection reset by (?:authenticating )?user (?P<user>\S+)"
    r" (?P<src_ip>\S+) port (?P<src_port>\d+)"
)

_PAM_SESSION_RE = re.compile(
    r"pam_unix\(sshd:session\): session (?P<action>opened|closed)"
    r" for user (?P<user>\S+)"
)


def decode_sshd(message: str) -> dict[str, str | int | None]:
    match = _INVALID_USER_RE.search(message)
    if match:
        return {
            "action": "invalid_user",
            "user": match.group("user"),
            "src_ip": match.group("src_ip"),
            "src_port": int(match.group("src_port")),
        }

    match = _ACCEPTED_RE.search(message)
    if match:
        return {
            "action": "accepted",
            "method": match.group("method"),
            "user": match.group("user"),
            "src_ip": match.group("src_ip"),
            "src_port": int(match.group("src_port")),
        }

    match = _FAILED_RE.search(message)
    if match:
        return {
            "action": "failed",
            "method": match.group("method"),
            "user": match.group("user"),
            "src_ip": match.group("src_ip"),
            "src_port": int(match.group("src_port")),
        }

    match = _CONN_RESET_RE.search(message)
    if match:
        return {
            "action": "connection_reset",
            "user": match.group("user"),
            "src_ip": match.group("src_ip"),
            "src_port": int(match.group("src_port")),
        }

    match = _DISCONNECTED_RE.search(message)
    if match:
        return {
            "action": "disconnected",
            "user": match.group("user"),
            "src_ip": match.group("src_ip"),
            "src_port": int(match.group("src_port")),
        }

    match = _CONN_CLOSED_RE.search(message)
    if match:
        return {
            "action": "connection_closed",
            "user": match.group("user"),
            "src_ip": match.group("src_ip"),
            "src_port": int(match.group("src_port")),
        }

    match = _PAM_SESSION_RE.search(message)
    if match:
        return {
            "action": f"session_{match.group('action')}",
            "user": match.group("user"),
        }

    return {}
