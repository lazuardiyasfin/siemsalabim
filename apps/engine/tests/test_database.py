import json
import pytest
import aiosqlite
from pathlib import Path
from unittest.mock import MagicMock

from src.database import init_db, get_db, store_events_and_alerts


@pytest.mark.asyncio
async def test_init_db_creates_tables_and_indexes(tmp_path: Path):
    """Test database creation, table schemas, and index creations."""
    test_db_path = tmp_path / "test_siem.db"

    await init_db(db_path=test_db_path)
    assert test_db_path.exists()

    async with aiosqlite.connect(test_db_path) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('events', 'alerts');"
        ) as cursor:
            tables = [row[0] for row in await cursor.fetchall()]
            assert "events" in tables
            assert "alerts" in tables

        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name IN ('idx_alerts_severity', 'idx_alerts_timestamp');"
        ) as cursor:
            indexes = [row[0] for row in await cursor.fetchall()]
            assert "idx_alerts_severity" in indexes
            assert "idx_alerts_timestamp" in indexes


@pytest.mark.asyncio
async def test_get_db_yields_connection(tmp_path: Path):
    """Test that the get_db generator yields a connection with active PRAGMAs."""
    test_db_path = tmp_path / "test_siem.db"
    await init_db(db_path=test_db_path)

    async for db in get_db(db_path=test_db_path):
        assert isinstance(db, aiosqlite.Connection)
        assert db.row_factory == aiosqlite.Row

        async with db.execute("PRAGMA foreign_keys;") as cursor:
            row = await cursor.fetchone()
            assert row[0] == 1
        break


@pytest.mark.asyncio
async def test_store_events_and_alerts_inserts_data(tmp_path: Path):
    """Test that store_events_and_alerts writes records to both tables correctly."""
    test_db_path = tmp_path / "test_siem.db"
    await init_db(db_path=test_db_path)

    mock_event = MagicMock()
    mock_event.program = "sshd"
    mock_event.model_dump_json.return_value = json.dumps(
        {"program": "sshd", "status": "failed"}
    )

    mock_alert = MagicMock()
    mock_alert.rule_id = "auth-01"
    mock_alert.rule_name = "Brute Force Detection"
    mock_alert.severity = "HIGH"
    mock_alert.description = "Multiple authentication failures detected."
    mock_alert.event_count = 5
    mock_alert.model_dump.return_value = {
        "source_events": [{"program": "sshd", "status": "failed"}]
    }

    await store_events_and_alerts(
        event=mock_event, alerts=[mock_alert], db_path=test_db_path
    )

    async with aiosqlite.connect(test_db_path) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM events;") as cursor:
            event_row = await cursor.fetchone()
            assert event_row is not None
            assert event_row["program"] == "sshd"
            assert json.loads(event_row["payload"]) == {
                "program": "sshd",
                "status": "failed",
            }

        async with db.execute("SELECT * FROM alerts;") as cursor:
            alert_row = await cursor.fetchone()
            assert alert_row is not None
            assert alert_row["rule_id"] == "auth-01"
            assert alert_row["severity"] == "HIGH"
            assert alert_row["event_count"] == 5
            assert json.loads(alert_row["source_events"]) == [
                {"program": "sshd", "status": "failed"}
            ]
