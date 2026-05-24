import pytest
import aiosqlite
from pathlib import Path
from src.database import init_db, get_db


@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path: Path):
    """Test database creation and table schemas."""
    test_db_path = tmp_path / "test_siem.db"

    await init_db(db_path=test_db_path)
    assert test_db_path.exists()

    async with aiosqlite.connect(test_db_path) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts';"
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == "alerts"


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
