from pathlib import Path

from src.models import LogFormat, PreDecodedLog
from src.parser.decoders import decode, init_decoders


def setup_module() -> None:
    """Load decoders from YAML before running tests."""
    decoders_dir = Path(__file__).parent.parent / "decoders"
    count = init_decoders(decoders_dir)
    assert count > 0, "No decoders loaded"


def _syslog_pre(program: str, message: str) -> PreDecodedLog:
    """Helper to create a syslog PreDecodedLog."""
    return PreDecodedLog(
        timestamp="2026-05-20T04:00:00+00:00",
        hostname="siem-target",
        program=program,
        pid=1234,
        message=message,
        log_format=LogFormat.SYSLOG,
    )


def _nginx_pre(line: str) -> PreDecodedLog:
    """Helper to create a nginx PreDecodedLog."""
    return PreDecodedLog(
        timestamp="19/May/2026:16:27:36 +0000",
        hostname="185.177.72.16",
        program="nginx",
        pid=None,
        message=line,
        log_format=LogFormat.NGINX_ACCESS,
    )


class TestSshdDecoder:
    """Tests for sshd YAML decoder."""

    def test_invalid_user(self) -> None:
        pre = _syslog_pre("sshd", "Invalid user fakeuser from 182.8.65.13 port 40908")
        result = decode(pre)

        assert result["action"] == "invalid_user"
        assert result["user"] == "fakeuser"
        assert result["src_ip"] == "182.8.65.13"
        assert result["src_port"] == 40908

    def test_accepted_publickey(self) -> None:
        pre = _syslog_pre(
            "sshd",
            "Accepted publickey for root from 182.8.65.13 port 40919 ssh2",
        )
        result = decode(pre)

        assert result["action"] == "accepted"
        assert result["method"] == "publickey"
        assert result["user"] == "root"

    def test_failed_password(self) -> None:
        pre = _syslog_pre("sshd", "Failed password for root from 1.2.3.4 port 22 ssh2")
        result = decode(pre)

        assert result["action"] == "failed"
        assert result["method"] == "password"

    def test_failed_password_invalid_user(self) -> None:
        pre = _syslog_pre(
            "sshd",
            "Failed password for invalid user admin from 5.6.7.8 port 443 ssh2",
        )
        result = decode(pre)

        assert result["action"] == "failed"
        assert result["user"] == "admin"

    def test_connection_closed_invalid_user(self) -> None:
        pre = _syslog_pre(
            "sshd",
            "Connection closed by invalid user admin 116.110.14.96 port 44718 [preauth]",
        )
        result = decode(pre)

        assert result["action"] == "connection_closed"
        assert result["src_ip"] == "116.110.14.96"

    def test_disconnected_invalid_user(self) -> None:
        pre = _syslog_pre(
            "sshd",
            "Disconnected from invalid user user3 94.26.106.201 port 26574 [preauth]",
        )
        result = decode(pre)

        assert result["action"] == "disconnected"
        assert result["user"] == "user3"

    def test_connection_reset(self) -> None:
        pre = _syslog_pre(
            "sshd",
            "Connection reset by authenticating user root 45.148.10.141 port 8882 [preauth]",
        )
        result = decode(pre)

        assert result["action"] == "connection_reset"
        assert result["user"] == "root"

    def test_pam_session_opened(self) -> None:
        pre = _syslog_pre(
            "sshd",
            "pam_unix(sshd:session): session opened for user root(uid=0) by root(uid=0)",
        )
        result = decode(pre)

        assert result["action"] == "session_opened"

    def test_unknown_message_returns_empty(self) -> None:
        pre = _syslog_pre("sshd", "Received signal 15; terminating.")
        result = decode(pre)

        assert result == {}


class TestNginxDecoder:
    """Tests for nginx YAML decoder."""

    def test_normal_get_200(self) -> None:
        line = '160.119.69.16 - - [19/May/2026:16:27:36 +0000] "GET / HTTP/1.1" 200 409 "-" "Mozilla/5.0"'
        pre = _nginx_pre(line)
        result = decode(pre)

        assert result["client_ip"] == "160.119.69.16"
        assert result["method"] == "GET"
        assert result["path"] == "/"
        assert result["status"] == 200

    def test_scanner_404(self) -> None:
        line = '185.177.72.16 - - [19/May/2026:21:46:44 +0000] "GET /.git/config HTTP/1.1" 404 134 "-" "curl/8.7.1"'
        pre = _nginx_pre(line)
        result = decode(pre)

        assert result["path"] == "/.git/config"
        assert result["status"] == 404

    def test_shodan_scanner(self) -> None:
        line = '176.65.139.66 - - [19/May/2026:18:59:32 +0000] "GET / HTTP/1.0" 200 615 "-" "Shodan-Pull/1.0"'
        pre = _nginx_pre(line)
        result = decode(pre)

        assert result["user_agent"] == "Shodan-Pull/1.0"

    def test_garbage_line_returns_empty(self) -> None:
        pre = _nginx_pre("not a log line")
        result = decode(pre)

        assert result == {}
