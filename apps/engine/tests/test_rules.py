from pathlib import Path

from src.models import Event, LogFormat
from src.rules import RuleEngine
from src.rules.loader import load_rules_from_dir, load_rules_from_file
from src.rules.matcher import RuleMatcher
from src.rules.models import FrequencyConfig, Rule, RuleCondition, Severity


def _make_sshd_event(action: str, user: str = "root", src_ip: str = "1.2.3.4") -> Event:
    """Helper to create an sshd Event for testing."""
    return Event(
        timestamp="2026-05-20T04:00:00+00:00",
        hostname="siem-target",
        program="sshd",
        pid=1234,
        log_format=LogFormat.SYSLOG,
        message=f"test {action} message",
        decoded={
            "action": action,
            "user": user,
            "src_ip": src_ip,
            "src_port": 22,
        },
        exporter_id="test",
        source_host="siem-target",
        source_path="/var/log/auth.log",
    )


def _make_nginx_event(
    status: int = 200,
    path: str = "/",
    client_ip: str = "5.6.7.8",
    user_agent: str = "curl/8.0",
) -> Event:
    """Helper to create a nginx Event for testing."""
    return Event(
        timestamp="19/May/2026:16:27:36 +0000",
        hostname=client_ip,
        program="nginx",
        pid=None,
        log_format=LogFormat.NGINX_ACCESS,
        message="test nginx line",
        decoded={
            "client_ip": client_ip,
            "method": "GET",
            "path": path,
            "status": status,
            "bytes": 100,
            "user_agent": user_agent,
        },
        exporter_id="test",
        source_host="siem-target",
        source_path="/var/log/nginx/access.log",
    )


class TestRuleLoader:
    """Tests for YAML rule loading."""

    def test_load_ssh_rules(self, tmp_path: Path) -> None:
        """Load rules from a valid YAML file."""
        yaml_content = """
rules:
  - id: test_rule
    name: Test Rule
    severity: high
    program: sshd
    conditions:
      - field: decoded.action
        value: failed
"""
        rule_file = tmp_path / "test.yaml"
        rule_file.write_text(yaml_content)

        rules = load_rules_from_file(rule_file)

        assert len(rules) == 1
        assert rules[0].id == "test_rule"
        assert rules[0].severity == Severity.HIGH

    def test_load_from_dir(self, tmp_path: Path) -> None:
        """Load rules from all YAML files in a directory."""
        for name in ["a.yaml", "b.yml"]:
            (tmp_path / name).write_text(
                "rules:\n  - id: %s\n    name: Rule\n    severity: low\n" % name
            )

        rules = load_rules_from_dir(tmp_path)

        assert len(rules) == 2

    def test_missing_dir_returns_empty(self, tmp_path: Path) -> None:
        """Non-existent directory returns empty list."""
        rules = load_rules_from_dir(tmp_path / "nonexistent")

        assert rules == []

    def test_corrupt_yaml_returns_empty(self, tmp_path: Path) -> None:
        """Corrupt YAML file returns empty list."""
        (tmp_path / "bad.yaml").write_text(": : : not yaml {{{}}")
        rules = load_rules_from_file(tmp_path / "bad.yaml")

        assert rules == []

    def test_missing_rules_key_returns_empty(self, tmp_path: Path) -> None:
        """YAML without 'rules' key returns empty list."""
        (tmp_path / "no_key.yaml").write_text("other_key: value\n")
        rules = load_rules_from_file(tmp_path / "no_key.yaml")

        assert rules == []


class TestRuleMatcherSingle:
    """Tests for single-event rule matching."""

    def test_match_sshd_invalid_user(self) -> None:
        """Rule matches sshd invalid_user event."""
        rule = Rule(
            id="test",
            name="Test",
            severity=Severity.MEDIUM,
            program="sshd",
            conditions=[RuleCondition(field="decoded.action", value="invalid_user")],
        )
        matcher = RuleMatcher([rule])
        event = _make_sshd_event("invalid_user", user="fakeuser")

        alerts = matcher.evaluate(event)

        assert len(alerts) == 1
        assert alerts[0].rule_id == "test"
        assert alerts[0].severity == Severity.MEDIUM

    def test_no_match_wrong_action(self) -> None:
        """Rule does not match when action differs."""
        rule = Rule(
            id="test",
            name="Test",
            severity=Severity.HIGH,
            program="sshd",
            conditions=[RuleCondition(field="decoded.action", value="failed")],
        )
        matcher = RuleMatcher([rule])
        event = _make_sshd_event("accepted")

        alerts = matcher.evaluate(event)

        assert alerts == []

    def test_no_match_wrong_program(self) -> None:
        """Rule does not match when program differs."""
        rule = Rule(
            id="test",
            name="Test",
            severity=Severity.LOW,
            program="nginx",
            conditions=[RuleCondition(field="decoded.action", value="invalid_user")],
        )
        matcher = RuleMatcher([rule])
        event = _make_sshd_event("invalid_user")

        alerts = matcher.evaluate(event)

        assert alerts == []

    def test_match_multiple_values(self) -> None:
        """Condition with list of values matches any."""
        rule = Rule(
            id="test",
            name="Test",
            severity=Severity.HIGH,
            program="sshd",
            conditions=[
                RuleCondition(field="decoded.action", value=["invalid_user", "failed"]),
            ],
        )
        matcher = RuleMatcher([rule])

        alerts1 = matcher.evaluate(_make_sshd_event("invalid_user"))
        alerts2 = matcher.evaluate(_make_sshd_event("failed"))
        alerts3 = matcher.evaluate(_make_sshd_event("accepted"))

        assert len(alerts1) == 1
        assert len(alerts2) == 1
        assert alerts3 == []

    def test_description_template(self) -> None:
        """Alert description has decoded fields substituted."""
        rule = Rule(
            id="test",
            name="Test",
            severity=Severity.MEDIUM,
            program="sshd",
            description="User '{user}' from {src_ip}",
            conditions=[RuleCondition(field="decoded.action", value="invalid_user")],
        )
        matcher = RuleMatcher([rule])
        event = _make_sshd_event("invalid_user", user="admin", src_ip="10.0.0.1")

        alerts = matcher.evaluate(event)

        assert "admin" in alerts[0].description
        assert "10.0.0.1" in alerts[0].description

    def test_match_nginx_status(self) -> None:
        """Rule matches nginx event by status code."""
        rule = Rule(
            id="test",
            name="Test",
            severity=Severity.HIGH,
            program="nginx",
            conditions=[RuleCondition(field="decoded.status", value="400")],
        )
        matcher = RuleMatcher([rule])

        alerts = matcher.evaluate(_make_nginx_event(status=400))

        assert len(alerts) == 1


class TestRuleMatcherFrequency:
    """Tests for frequency-based rule matching."""

    def test_fires_at_threshold(self) -> None:
        """Frequency rule fires after N events from same IP."""
        rule = Rule(
            id="brute",
            name="Brute Force",
            severity=Severity.CRITICAL,
            program="sshd",
            conditions=[RuleCondition(field="decoded.action", value="invalid_user")],
            frequency=FrequencyConfig(
                count=3, window_seconds=60, group_by="decoded.src_ip"
            ),
        )
        matcher = RuleMatcher([rule])

        event = _make_sshd_event("invalid_user", src_ip="1.2.3.4")

        assert matcher.evaluate(event) == []  # 1
        assert matcher.evaluate(event) == []  # 2
        alerts = matcher.evaluate(event)  # 3 → fires
        assert len(alerts) == 1
        assert alerts[0].event_count == 3

    def test_different_ips_tracked_separately(self) -> None:
        """Events from different IPs don't count together."""
        rule = Rule(
            id="brute",
            name="Brute Force",
            severity=Severity.CRITICAL,
            program="sshd",
            conditions=[RuleCondition(field="decoded.action", value="failed")],
            frequency=FrequencyConfig(
                count=3, window_seconds=60, group_by="decoded.src_ip"
            ),
        )
        matcher = RuleMatcher([rule])

        for _ in range(2):
            matcher.evaluate(_make_sshd_event("failed", src_ip="1.1.1.1"))
            matcher.evaluate(_make_sshd_event("failed", src_ip="2.2.2.2"))

        # Neither IP reached count=3 yet.
        assert matcher.evaluate(_make_sshd_event("failed", src_ip="1.1.1.1")) != []
        assert matcher.evaluate(_make_sshd_event("failed", src_ip="2.2.2.2")) != []

    def test_resets_after_alert(self) -> None:
        """After alert fires, counter resets."""
        rule = Rule(
            id="brute",
            name="Brute Force",
            severity=Severity.CRITICAL,
            program="sshd",
            conditions=[RuleCondition(field="decoded.action", value="failed")],
            frequency=FrequencyConfig(
                count=2, window_seconds=60, group_by="decoded.src_ip"
            ),
        )
        matcher = RuleMatcher([rule])
        event = _make_sshd_event("failed", src_ip="1.1.1.1")

        matcher.evaluate(event)  # 1
        alerts1 = matcher.evaluate(event)  # 2 → fires
        assert len(alerts1) == 1

        # Counter reset, need 2 more.
        assert matcher.evaluate(event) == []  # 1 again
        alerts2 = matcher.evaluate(event)  # 2 → fires again
        assert len(alerts2) == 1


class TestRuleEngineIntegration:
    """Integration tests using real YAML rule files."""

    def test_load_project_rules(self) -> None:
        """Load rules from the project's rules directory."""
        rules_dir = Path(__file__).parent.parent / "rules"
        if not rules_dir.exists():
            return  # skip if rules dir not found in test environment

        engine = RuleEngine(rules_dir)

        event = _make_sshd_event("invalid_user", user="admin", src_ip="116.110.14.96")
        alerts = engine.evaluate(event)

        assert len(alerts) >= 1
        assert any(a.rule_id == "ssh_invalid_user" for a in alerts)
