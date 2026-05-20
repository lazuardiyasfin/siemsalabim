from src.parser.decoders.nginx import decode_nginx
from src.parser.decoders.sshd import decode_sshd


class TestSshdDecoder:
    def test_invalid_user(self) -> None:
        msg = "Invalid user fakeuser from 182.8.65.13 port 40908"
        result = decode_sshd(msg)

        assert result["action"] == "invalid_user"
        assert result["user"] == "fakeuser"
        assert result["src_ip"] == "182.8.65.13"
        assert result["src_port"] == 40908

    def test_accepted_publickey(self) -> None:
        msg = (
            "Accepted publickey for root from 182.8.65.13 port 40919 ssh2:"
            " ED25519 SHA256:5JRnbBDanAan4ALR0Gj/QNstv4gBfX/Xq45+2TZ1Rhc"
        )
        result = decode_sshd(msg)

        assert result["action"] == "accepted"
        assert result["method"] == "publickey"
        assert result["user"] == "root"
        assert result["src_ip"] == "182.8.65.13"

    def test_failed_password(self) -> None:
        msg = "Failed password for root from 1.2.3.4 port 22 ssh2"
        result = decode_sshd(msg)

        assert result["action"] == "failed"
        assert result["method"] == "password"
        assert result["user"] == "root"

    def test_failed_password_invalid_user(self) -> None:
        msg = "Failed password for invalid user admin from 5.6.7.8 port 443 ssh2"
        result = decode_sshd(msg)

        assert result["action"] == "failed"
        assert result["user"] == "admin"

    def test_connection_closed_invalid_user(self) -> None:
        msg = (
            "Connection closed by invalid user admin 116.110.14.96 port 44718 [preauth]"
        )
        result = decode_sshd(msg)

        assert result["action"] == "connection_closed"
        assert result["src_ip"] == "116.110.14.96"

    def test_disconnected_invalid_user(self) -> None:
        msg = "Disconnected from invalid user user3 94.26.106.201 port 26574 [preauth]"
        result = decode_sshd(msg)

        assert result["action"] == "disconnected"
        assert result["user"] == "user3"
        assert result["src_ip"] == "94.26.106.201"

    def test_connection_reset(self) -> None:
        msg = (
            "Connection reset by authenticating user root"
            " 45.148.10.141 port 8882 [preauth]"
        )
        result = decode_sshd(msg)

        assert result["action"] == "connection_reset"
        assert result["user"] == "root"
        assert result["src_ip"] == "45.148.10.141"

    def test_pam_session_opened(self) -> None:
        msg = (
            "pam_unix(sshd:session): session opened for user root(uid=0) by root(uid=0)"
        )
        result = decode_sshd(msg)

        assert result["action"] == "session_opened"
        assert result["user"] == "root(uid=0)"

    def test_unknown_message_returns_empty(self) -> None:
        result = decode_sshd("Received signal 15; terminating.")

        assert result == {}


class TestNginxDecoder:
    def test_normal_get_200(self) -> None:
        line = (
            "160.119.69.16 - - [19/May/2026:16:27:36 +0000]"
            ' "GET / HTTP/1.1" 200 409 "-" "Mozilla/5.0"'
        )
        result = decode_nginx(line)

        assert result["client_ip"] == "160.119.69.16"
        assert result["method"] == "GET"
        assert result["path"] == "/"
        assert result["status"] == 200
        assert result["bytes"] == 409
        assert result["referer"] is None
        assert result["user_agent"] == "Mozilla/5.0"

    def test_scanner_404(self) -> None:
        line = (
            "185.177.72.16 - - [19/May/2026:21:46:44 +0000]"
            ' "GET /.git/config HTTP/1.1" 404 134 "-" "curl/8.7.1"'
        )
        result = decode_nginx(line)

        assert result["path"] == "/.git/config"
        assert result["status"] == 404
        assert result["user_agent"] == "curl/8.7.1"

    def test_post_with_referer(self) -> None:
        line = (
            "176.65.139.140 - - [19/May/2026:16:49:24 +0000]"
            ' "POST /boaform/admin/formLogin HTTP/1.1" 404 134'
            ' "http://143.198.194.101:80/admin/login.asp"'
            ' "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0)'
            ' Gecko/20100101 Firefox/71.0"'
        )
        result = decode_nginx(line)

        assert result["method"] == "POST"
        assert result["path"] == "/boaform/admin/formLogin"
        assert result["referer"] == "http://143.198.194.101:80/admin/login.asp"

    def test_shodan_scanner(self) -> None:
        line = (
            "176.65.139.66 - - [19/May/2026:18:59:32 +0000]"
            ' "GET / HTTP/1.0" 200 615 "-" "Shodan-Pull/1.0"'
        )
        result = decode_nginx(line)

        assert result["user_agent"] == "Shodan-Pull/1.0"
        assert result["protocol"] == "HTTP/1.0"

    def test_garbage_line_returns_empty(self) -> None:
        result = decode_nginx("not a log line")

        assert result == {}
