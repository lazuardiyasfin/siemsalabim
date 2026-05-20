from datetime import datetime, timezone

from src.models import LogFormat, RawLog
from src.parser import parse


class TestParseIntegration:
    def test_sshd_invalid_user_full(self) -> None:
        raw = RawLog(
            exporter_id="target-prod-01",
            host="siem-target",
            path="/var/log/auth.log",
            line=(
                "2026-05-20T04:03:49.940072+00:00 siem-target sshd[22184]:"
                " Invalid user fakeuser from 182.8.65.13 port 40908"
            ),
            received_at=datetime.now(tz=timezone.utc),
        )

        event = parse(raw)

        assert event is not None
        assert event.log_format == LogFormat.SYSLOG
        assert event.program == "sshd"
        assert event.pid == 22184
        assert event.decoded["action"] == "invalid_user"
        assert event.decoded["user"] == "fakeuser"
        assert event.decoded["src_ip"] == "182.8.65.13"
        assert event.exporter_id == "target-prod-01"
        assert event.source_path == "/var/log/auth.log"

    def test_nginx_get_full(self) -> None:
        raw = RawLog(
            exporter_id="target-prod-01",
            host="siem-target",
            path="/var/log/nginx/access.log",
            line=(
                "185.177.72.16 - - [19/May/2026:21:46:44 +0000]"
                ' "GET /.git/config HTTP/1.1" 404 134 "-" "curl/8.7.1"'
            ),
            received_at=datetime.now(tz=timezone.utc),
        )

        event = parse(raw)

        assert event is not None
        assert event.log_format == LogFormat.NGINX_ACCESS
        assert event.decoded["path"] == "/.git/config"
        assert event.decoded["status"] == 404
        assert event.decoded["client_ip"] == "185.177.72.16"

    def test_unparseable_line_returns_none(self) -> None:
        raw = RawLog(
            exporter_id="test",
            host="test",
            path="/tmp/random.log",
            line="this is not a valid log line",
            received_at=datetime.now(tz=timezone.utc),
        )

        assert parse(raw) is None

    def test_syslog_without_decoder(self) -> None:
        raw = RawLog(
            exporter_id="test",
            host="siem-target",
            path="/var/log/auth.log",
            line=(
                "2026-05-19T16:15:01.958277+00:00 siem-target CRON[17829]:"
                " pam_unix(cron:session): session opened for user root(uid=0)"
                " by root(uid=0)"
            ),
            received_at=datetime.now(tz=timezone.utc),
        )

        event = parse(raw)

        assert event is not None
        assert event.program == "CRON"
        assert event.decoded == {}
