import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

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
        await db.commit()


async def get_db(db_path: Path = DB_PATH):
    """Dependency generator."""
    async with get_db_session(db_path) as db:
        yield db
