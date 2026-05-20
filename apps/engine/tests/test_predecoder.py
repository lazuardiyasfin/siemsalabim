from src.models import LogFormat
from src.parser.predecoder import predecode


class TestSyslogPredecode:
    def test_sshd_invalid_user(self) -> None:
        line = (
            "2026-05-20T04:03:49.940072+00:00 siem-target sshd[22184]:"
            " Invalid user fakeuser from 182.8.65.13 port 40908"
        )
        result = predecode(line, "/var/log/auth.log")

        assert result is not None
        assert result.log_format == LogFormat.SYSLOG
        assert result.timestamp == "2026-05-20T04:03:49.940072+00:00"
        assert result.hostname == "siem-target"
        assert result.program == "sshd"
        assert result.pid == 22184
        assert "Invalid user fakeuser" in result.message

    def test_sshd_accepted(self) -> None:
        line = (
            "2026-05-20T04:02:55.999789+00:00 siem-target sshd[22021]:"
            " Accepted publickey for root from 182.8.65.13 port 40919 ssh2:"
            " ED25519 SHA256:5JRnbBDanAan4ALR0Gj/QNstv4gBfX/Xq45+2TZ1Rhc"
        )
        result = predecode(line, "/var/log/auth.log")

        assert result is not None
        assert result.program == "sshd"
        assert result.pid == 22021

    def test_pam_session(self) -> None:
        line = (
            "2026-05-20T04:02:56.002482+00:00 siem-target sshd[22021]:"
            " pam_unix(sshd:session): session opened for user root(uid=0)"
            " by root(uid=0)"
        )
        result = predecode(line, "/var/log/auth.log")

        assert result is not None
        assert result.program == "sshd"

    def test_cron_line(self) -> None:
        line = (
            "2026-05-19T16:15:01.958277+00:00 siem-target CRON[17829]:"
            " pam_unix(cron:session): session opened for user root(uid=0)"
            " by root(uid=0)"
        )
        result = predecode(line, "/var/log/auth.log")

        assert result is not None
        assert result.program == "CRON"
        assert result.pid == 17829

    def test_systemd_logind(self) -> None:
        line = (
            "2026-05-20T04:02:56.020984+00:00 siem-target systemd-logind[836]:"
            " New session 88 of user root."
        )
        result = predecode(line, "/var/log/auth.log")

        assert result is not None
        assert result.program == "systemd-logind"
        assert result.pid == 836


class TestNginxPredecode:
    def test_normal_get(self) -> None:
        line = (
            "160.119.69.16 - - [19/May/2026:16:27:36 +0000]"
            ' "GET / HTTP/1.1" 200 409 "-" "Mozilla/5.0"'
        )
        result = predecode(line, "/var/log/nginx/access.log")

        assert result is not None
        assert result.log_format == LogFormat.NGINX_ACCESS
        assert result.hostname == "160.119.69.16"
        assert result.program == "nginx"

    def test_404_scanner(self) -> None:
        line = (
            "185.177.72.16 - - [19/May/2026:21:46:44 +0000]"
            ' "GET /.git/config HTTP/1.1" 404 134 "-" "curl/8.7.1"'
        )
        result = predecode(line, "/var/log/nginx/access.log")

        assert result is not None
        assert result.log_format == LogFormat.NGINX_ACCESS

    def test_unknown_line_returns_none(self) -> None:
        result = predecode("this is not a log line at all", "")

        assert result is None

    def test_auto_detect_syslog(self) -> None:
        line = (
            "2026-05-20T04:03:49.940072+00:00 siem-target sshd[22184]:"
            " Invalid user test from 1.2.3.4 port 22"
        )
        result = predecode(line, "")

        assert result is not None
        assert result.log_format == LogFormat.SYSLOG
