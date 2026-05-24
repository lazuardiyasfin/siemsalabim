import json
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

from .models import Event
from .rules.models import Alert

DB_PATH = Path("siem.db")


@asynccontextmanager
async def get_db_session(db_path: Path = DB_PATH):
    """Context manager to automatically open, configure, and close the connection."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON;")
        yield db


async def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize the database, enable WAL mode, and create tables."""
    async with get_db_session(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                program TEXT NOT NULL,
                payload TEXT NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                rule_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                event_count INTEGER NOT NULL DEFAULT 1,
                source_events TEXT NOT NULL
            );
        """)

        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC);"
        )

        await db.commit()


async def get_db(db_path: Path = DB_PATH):
    """Dependency generator."""
    async with get_db_session(db_path) as db:
        yield db


async def store_events_and_alerts(
    event: Event, alerts: list[Alert], db_path: Path = DB_PATH
) -> None:
    """Inserts an ingested event and any triggered security alerts into the DB safely."""
    async with get_db_session(db_path) as db:
        event_json_str = event.model_dump_json()

        await db.execute(
            "INSERT INTO events (program, payload) VALUES (?, ?);",
            (event.program, event_json_str),
        )

        for alert in alerts:
            alert_data = alert.model_dump(mode="json")
            source_events_str = json.dumps(alert_data.get("source_events", []))

            await db.execute(
                """
                INSERT INTO alerts 
                (rule_id, rule_name, severity, description, event_count, source_events) 
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    alert.rule_id,
                    alert.rule_name,
                    alert.severity,
                    alert.description,
                    alert.event_count,
                    source_events_str,
                ),
            )

        await db.commit()
