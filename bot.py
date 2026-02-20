import logging
import discord
from discord.ext import tasks
from config import TOKEN, GUILD_ID, TARGET_CHANNELS, CHECK_INTERVAL_HOURS, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, TEST_MODE
from cleanup import process_channel
from database import init_db, close_db
from logging_config import setup_logging

# Setup logging before creating logger
setup_logging(log_file=LOG_FILE, max_bytes=LOG_MAX_BYTES, backup_count=LOG_BACKUP_COUNT)
_logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    _logger.info("Logged in as %s (TEST_MODE=%s)", bot.user, TEST_MODE)
    await init_db()

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        _logger.warning("Bot not a member of guild %s; scheduled cleanup will still run when guild becomes available", GUILD_ID)

    # Initial cleanup run (only for available channels)
    for channel_id in TARGET_CHANNELS:
        if not guild:
            _logger.debug("Skipping initial run for channel %s because guild is not available", channel_id)
            continue
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await process_channel(channel)
            except Exception:
                _logger.exception("Initial processing failed for channel %s", channel_id)

    cleanup_loop.start()


@tasks.loop(hours=CHECK_INTERVAL_HOURS)
async def cleanup_loop():
    _logger.info("Running scheduled cleanup...")
    guild = bot.get_guild(GUILD_ID)

    for channel_id in TARGET_CHANNELS:
        if not guild:
            _logger.debug("Guild %s not available yet; skipping channel %s", GUILD_ID, channel_id)
            continue
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await process_channel(channel)
            except Exception:
                _logger.exception("Scheduled processing failed for channel %s", channel_id)


@bot.event
async def on_disconnect():
    _logger.info("Bot disconnecting, closing database connection")
    try:
        await close_db()
    except Exception:
        _logger.exception("Error while closing database")


bot.run(TOKEN)
