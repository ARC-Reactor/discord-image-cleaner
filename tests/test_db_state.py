import os
import importlib
import asyncio


def test_channel_state(tmp_path):
    os.environ.update({
        "DISCORD_TOKEN": "dummy",
        "GUILD_ID": "123",
        "TARGET_CHANNELS": "123",
        "TEST_MODE": "true",
        "DATABASE_FILE": str(tmp_path / "image_tracker_state.db"),
    })

    import config as _config
    importlib.reload(_config)

    db = importlib.import_module("database")
    importlib.reload(db)

    asyncio.run(db.init_db())
    asyncio.run(db.upsert_channel_state(42, 5555, "2020-01-01T00:00:00Z"))
    lm, ldt = asyncio.run(db.get_channel_state(42))
    assert lm == 5555
    assert ldt == "2020-01-01T00:00:00Z"
    asyncio.run(db.close_db())
