"""Handles two formats observed on the target VPS:

1. Syslog RFC 5424 (auth.log, syslog):
   ``2026-05-20T04:03:49.940072+00:00 siem-target sshd[22184]: message``

2. Nginx combined access log:
   ``185.177.72.16 - - [19/May/2026:21:46:44 +0000] "GET / HTTP/1.1" 200 ...``
"""

import logging
import re

from ..models import LogFormat, PreDecodedLog

logger = logging.getLogger(__name__)

_SYSLOG_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2})"
    r"\s+(?P<hostname>\S+)"
    r"\s+(?P<program>[A-Za-z0-9_.\-]+)"
    r"(?:\[(?P<pid>\d+)\])?"
    r":\s+(?P<message>.+)$"
)

_NGINX_RE = re.compile(
    r"^(?P<client_ip>\S+)"
    r"\s+\S+"  # ident
    r"\s+\S+"  # auth user
    r"\s+\[(?P<timestamp>[^\]]+)\]"
    r'\s+"(?P<request>[^"]*)"'
    r"\s+(?P<status>\d{3})"
    r"\s+(?P<bytes>\d+)"
    r'\s+"(?P<referer>[^"]*)"'
    r'\s+"(?P<user_agent>[^"]*)"'
)

_NGINX_PARTIAL_RE = re.compile(
    r"^(?P<client_ip>\S+)"
    r"\s+\S+"
    r"\s+\S+"
    r"\s+\[(?P<timestamp>[^\]]+)\]"
    r"\s+(?P<message>.+)$"
)


def predecode(line: str, source_path: str = "") -> PreDecodedLog | None:
    if _is_nginx_path(source_path):
        return _try_nginx(line)

    if _is_syslog_path(source_path):
        return _try_syslog(line)

    return _try_syslog(line) or _try_nginx(line)


def _is_nginx_path(path: str) -> bool:
    return "nginx" in path and "access" in path


def _is_syslog_path(path: str) -> bool:
    return any(name in path for name in ("auth.log", "syslog", "messages"))


def _try_syslog(line: str) -> PreDecodedLog | None:
    match = _SYSLOG_RE.match(line)
    if not match:
        return None

    pid_str = match.group("pid")
    return PreDecodedLog(
        timestamp=match.group("timestamp"),
        hostname=match.group("hostname"),
        program=match.group("program"),
        pid=int(pid_str) if pid_str else None,
        message=match.group("message"),
        log_format=LogFormat.SYSLOG,
    )


def _try_nginx(line: str) -> PreDecodedLog | None:
    match = _NGINX_RE.match(line)
    if match:
        return PreDecodedLog(
            timestamp=match.group("timestamp"),
            hostname=match.group("client_ip"),
            program="nginx",
            pid=None,
            message=line,
            log_format=LogFormat.NGINX_ACCESS,
        )

    match = _NGINX_PARTIAL_RE.match(line)
    if match:
        return PreDecodedLog(
            timestamp=match.group("timestamp"),
            hostname=match.group("client_ip"),
            program="nginx",
            pid=None,
            message=line,
            log_format=LogFormat.NGINX_ACCESS,
        )

    return None
