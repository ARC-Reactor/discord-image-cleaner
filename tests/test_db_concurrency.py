import os
import importlib
import asyncio
import aiosqlite


async def _concurrent_inserts(db_module, db_path, n=50):
    # schedule many concurrent insert_record calls
    tasks = []
    for i in range(n):
        tasks.append(db_module.insert_record(1000 + i, 1, "2020-01-01T00:00:00Z", f"/tmp/f{i}.png"))
    await asyncio.gather(*tasks)


def test_db_concurrency(tmp_path):
    os.environ.update({
        "DISCORD_TOKEN": "dummy",
        "GUILD_ID": "123",
        "TARGET_CHANNELS": "123",
        "TEST_MODE": "true",
        "DATABASE_FILE": str(tmp_path / "image_tracker_concurrency.db"),
    })

    # reload config first so DATABASE_FILE is read from the updated env
    import config as _config
    importlib.reload(_config)
    db = importlib.import_module("database")
    importlib.reload(db)

    asyncio.run(db.init_db())
    asyncio.run(_concurrent_inserts(db, os.environ["DATABASE_FILE"], n=100))

    # verify count using the same DB connection object
    async def _count_using_module():
        cur = await db._db.execute("SELECT COUNT(*) FROM tracked_images")
        row = await cur.fetchone()
        return row[0]

    count = asyncio.run(_count_using_module())
    assert count >= 100
    asyncio.run(db.close_db())
