import os
import aiosqlite
import logging
from pathlib import Path
from config import DATABASE_FILE

_logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tracked_images (
    message_id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    created_at TEXT,
    file_path TEXT,
    deleted INTEGER DEFAULT 0
);
"""

CREATE_CHANNEL_STATE_SQL = """
CREATE TABLE IF NOT EXISTS channel_state (
    channel_id INTEGER PRIMARY KEY,
    last_message_id INTEGER,
    last_processed_at TEXT
);
"""

_db = None

def _ensure_database_path(db_path: str) -> None:
    """Ensure the database file can be created/opened. Raise clear errors for common Docker issues."""
    path = Path(db_path)
    parent = path.parent
    if path.exists():
        if path.is_dir():
            raise RuntimeError(
                "Database path is a directory, not a file: %s. "
                "With Docker, bind-mounting a missing file creates a directory. "
                "Use a data directory instead, e.g. -v ./data:/app/data and DATABASE_FILE=/app/data/image_tracker.db"
                % db_path
            )
    else:
        parent.mkdir(parents=True, exist_ok=True)
        path.touch()

async def init_db():
    """Initialize a single aiosqlite connection and create table."""
    global _db
    if _db:
        return
    _ensure_database_path(DATABASE_FILE)
    _db = await aiosqlite.connect(DATABASE_FILE)
    await _db.execute(CREATE_TABLE_SQL)
    await _db.execute(CREATE_CHANNEL_STATE_SQL)
    await _db.commit()
    _logger.info("Database initialized at %s", DATABASE_FILE)

async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None

async def insert_record(message_id, channel_id, created_at, file_path):
    global _db
    if not _db:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    try:
        await _db.execute(
            "INSERT OR IGNORE INTO tracked_images (message_id, channel_id, created_at, file_path, deleted) VALUES (?, ?, ?, ?, 0)",
            (message_id, channel_id, created_at, file_path),
        )
        await _db.commit()
    except Exception as e:
        _logger.exception("Failed to insert record for message %s: %s", message_id, e)


async def get_channel_state(channel_id):
    """Return (last_message_id, last_processed_at) for a channel, or (None, None)."""
    global _db
    if not _db:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    try:
        cur = await _db.execute(
            "SELECT last_message_id, last_processed_at FROM channel_state WHERE channel_id=?",
            (channel_id,),
        )
        row = await cur.fetchone()
        if row:
            return row[0], row[1]
        return None, None
    except Exception as e:
        _logger.exception("Failed to get channel state for %s: %s", channel_id, e)
        return None, None


async def upsert_channel_state(channel_id, last_message_id, last_processed_at):
    global _db
    if not _db:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    try:
        await _db.execute(
            "INSERT INTO channel_state (channel_id, last_message_id, last_processed_at) VALUES (?, ?, ?)"
            " ON CONFLICT(channel_id) DO UPDATE SET last_message_id=excluded.last_message_id, last_processed_at=excluded.last_processed_at",
            (channel_id, last_message_id, last_processed_at),
        )
        await _db.commit()
    except Exception as e:
        _logger.exception("Failed to upsert channel state for %s: %s", channel_id, e)

async def mark_deleted(message_id):
    global _db
    if not _db:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    try:
        await _db.execute(
            "UPDATE tracked_images SET deleted=1 WHERE message_id=?",
            (message_id,),
        )
        await _db.commit()
    except Exception as e:
        _logger.exception("Failed to mark message %s deleted: %s", message_id, e)
