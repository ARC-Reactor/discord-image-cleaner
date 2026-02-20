import asyncio
import os
import re
import logging
import discord
from uuid import uuid4
from pathlib import Path
from datetime import datetime, timedelta, timezone
from config import DAYS_OLD, ARCHIVE_FOLDER, TEST_MODE, MAX_ARCHIVE_SIZE_MB, FILE_TYPES
from database import insert_record, mark_deleted, get_channel_state, upsert_channel_state

_logger = logging.getLogger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]")
BATCH_SIZE = 200


def sanitize_filename(filename: str) -> str:
    """Return a filesystem-safe filename (no path components)."""
    base_name = os.path.basename(filename or "attachment")
    safe = _SAFE_FILENAME_RE.sub("_", base_name)
    return safe


def prune_archive(base_path: Path, max_bytes: int) -> int:
    """Prune files under base_path until total size <= max_bytes.

    Returns number of bytes freed.
    """
    if max_bytes <= 0:
        return 0

    files = []
    total = 0
    for root, _, filenames in os.walk(base_path):
        for fn in filenames:
            fp = Path(root) / fn
            try:
                sz = fp.stat().st_size
            except FileNotFoundError:
                continue
            total += sz
            files.append((fp, fp.stat().st_mtime, sz))

    if total <= max_bytes:
        return 0

    # sort by mtime ascending (oldest first)
    files.sort(key=lambda x: x[1])
    freed = 0
    for fp, _, sz in files:
        try:
            fp.unlink()
            freed += sz
        except FileNotFoundError:
            continue
        if total - freed <= max_bytes:
            break

    return freed


async def process_channel(channel):
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_OLD)

    base_archive = Path(ARCHIVE_FOLDER)
    base_archive.mkdir(parents=True, exist_ok=True)

    # enforce archive quota if configured
    if MAX_ARCHIVE_SIZE_MB and MAX_ARCHIVE_SIZE_MB > 0:
        max_bytes = MAX_ARCHIVE_SIZE_MB * 1024 * 1024
        try:
            freed = prune_archive(base_archive, max_bytes)
            if freed:
                _logger.info("Pruned archive %s freed %d bytes", base_archive, freed)
        except Exception:
            _logger.exception("Error while pruning archive %s", base_archive)

    # Use incremental scanning: read last processed message id for this channel and page forward
    last_message_id, _ = await get_channel_state(channel.id)
    after = discord.Object(id=last_message_id) if last_message_id else None
    processed_max = last_message_id or 0

    while True:
        batch = []
        batch_start = datetime.now(timezone.utc)
        async for message in channel.history(limit=BATCH_SIZE, after=after, before=cutoff, oldest_first=True):
            batch.append(message)

        if not batch:
            break

        batch_count = 0
        batch_errors = 0

        for message in batch:
            try:
                if not message.attachments:
                    continue

                for attachment in message.attachments:
                    filename = attachment.filename or "attachment"
                    if not filename.lower().endswith(FILE_TYPES):
                        continue

                    # sanitize and uniquify filename
                    base_name = os.path.basename(filename)
                    safe = _SAFE_FILENAME_RE.sub("_", base_name)
                    unique_prefix = f"{message.id}_"
                    if getattr(attachment, "id", None) is None:
                        unique_prefix += uuid4().hex + "_"
                    else:
                        unique_prefix += str(attachment.id) + "_"

                    folder = base_archive / str(channel.id) / message.created_at.strftime("%Y-%m-%d")
                    folder.mkdir(parents=True, exist_ok=True)

                    file_path = folder / (unique_prefix + safe)

                    try:
                        if not file_path.exists():
                            await attachment.save(str(file_path))
                    except Exception:
                        _logger.exception("Failed to save attachment %s from message %s", filename, message.id)
                        continue

                    await insert_record(
                        message.id,
                        channel.id,
                        message.created_at.isoformat(),
                        str(file_path),
                    )

                    if TEST_MODE:
                        _logger.info("[TEST MODE] Would delete message %s", message.id)
                    else:
                        # permission check
                        perms = channel.permissions_for(channel.guild.me)
                        if not perms.manage_messages:
                            _logger.warning("Missing manage_messages permission in channel %s; skipping delete for %s", channel.id, message.id)
                            continue

                        try:
                            await message.delete()
                            await mark_deleted(message.id)
                            _logger.info("Deleted message %s", message.id)
                            await asyncio.sleep(0.2)
                        except Exception:
                            _logger.exception("Failed to delete message %s", message.id)

                processed_max = max(processed_max, message.id)
                batch_count += 1

            except Exception:
                batch_errors += 1
                _logger.exception("Error processing message %s in channel %s", getattr(message, "id", "?"), channel.id)

        # Always advance cursor past the batch we've seen so we don't get stuck when
        # a batch has no/few matching attachments (which would otherwise never update processed_max).
        batch_max_id = max(message.id for message in batch)
        processed_max = max(processed_max, batch_max_id)
        prev_last = last_message_id or 0

        # update cursor in memory for pagination (next batch)
        last_message_id = processed_max
        after = discord.Object(id=processed_max)

        # Only persist channel state when we actually deleted messages. In TEST_MODE do not
        # persist, so a later run with TEST_MODE=false will re-scan and delete those messages.
        if not TEST_MODE and processed_max and processed_max != prev_last:
            await upsert_channel_state(channel.id, processed_max, datetime.now(timezone.utc).isoformat())

        batch_duration = (datetime.now(timezone.utc) - batch_start).total_seconds()
        _logger.info(
            "Processed batch for channel %s: messages=%d errors=%d duration=%.2fs",
            channel.id,
            batch_count,
            batch_errors,
            batch_duration,
        )

        if len(batch) < BATCH_SIZE:
            break
