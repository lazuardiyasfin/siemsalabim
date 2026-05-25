import pytest

from src.exporter_manager import ExporterManager


class TestExporterManager:
    """Tests for exporter connection tracking."""

    def test_register_and_list(self) -> None:
        """Registered exporter appears in list."""
        mgr = ExporterManager()
        mgr.register("node-01", "fake-ws")

        assert "node-01" in mgr.get_exporter_ids()

    def test_unregister(self) -> None:
        """Unregistered exporter is removed from list."""
        mgr = ExporterManager()
        mgr.register("node-01", "fake-ws")
        mgr.unregister("node-01")

        assert "node-01" not in mgr.get_exporter_ids()

    def test_unregister_nonexistent(self) -> None:
        """Unregistering unknown ID does not crash."""
        mgr = ExporterManager()
        mgr.unregister("nonexistent")

    def test_empty_list(self) -> None:
        """Empty manager returns empty list."""
        mgr = ExporterManager()

        assert mgr.get_exporter_ids() == []

    @pytest.mark.asyncio
    async def test_send_command_no_exporter(self) -> None:
        """Sending to unknown exporter returns False."""
        mgr = ExporterManager()

        result = await mgr.send_command("nonexistent", {"type": "test"})

        assert result is False

    def test_multiple_exporters(self) -> None:
        """Multiple exporters tracked independently."""
        mgr = ExporterManager()
        mgr.register("node-01", "ws1")
        mgr.register("node-02", "ws2")

        ids = mgr.get_exporter_ids()
        assert "node-01" in ids
        assert "node-02" in ids

        mgr.unregister("node-01")
        assert "node-01" not in mgr.get_exporter_ids()
        assert "node-02" in mgr.get_exporter_ids()
