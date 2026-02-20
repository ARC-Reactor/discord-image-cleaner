import os
import importlib
import asyncio


def test_smoke(tmp_path):
    # Set required env vars before importing project modules
    os.environ.update(
        {
            "DISCORD_TOKEN": "dummy",
            "GUILD_ID": "123",
            "TARGET_CHANNELS": "123",
            "TEST_MODE": "true",
            # Put the database file in the temporary path so tests don't pollute the repo
            "DATABASE_FILE": str(tmp_path / "image_tracker_test.db"),
        }
    )

    # Import/reload config and database module so they pick up the test DATABASE_FILE
    import config as _config
    importlib.reload(_config)

    db = importlib.import_module("database")
    importlib.reload(db)

    asyncio.run(db.init_db())

    # check that the DB file path reported by config exists via the module connection
    import config
    assert config.DATABASE_FILE == str(tmp_path / "image_tracker_test.db")

    # ensure the table exists
    async def _check_table():
        cur = await db._db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracked_images'")
        row = await cur.fetchone()
        return row is not None

    assert asyncio.run(_check_table())

    asyncio.run(db.close_db())
