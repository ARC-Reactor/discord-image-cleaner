import os
from pathlib import Path
from dotenv import load_dotenv
from filetypes import MANAGED_EXTENSIONS

load_dotenv()


def _get_bool_env(name: str, default: bool) -> bool:
	"""Parse a boolean environment variable in a user-friendly way.

	Accepts: 1, true, yes, y, on, 0, false, no, n, off (case-insensitive).
	Strips surrounding quotes and carriage returns so "false", 'true', etc. work.
	"""
	raw = os.getenv(name)
	if raw is None or (raw := raw.strip()) == "":
		return default

	# Strip optional surrounding single/double quotes (e.g. "false" or 'true')
	if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
		raw = raw[1:-1]
	val = raw.strip().replace("\r", "").lower()
	if not val:
		return default

	if val in ("1", "true", "yes", "y", "on"):
		return True
	if val in ("0", "false", "no", "n", "off"):
		return False

	raise RuntimeError(
		f"{name} must be one of: 1, 0, true, false, yes, no, on, off (case-insensitive); got {raw!r}"
	)


# Basic env parsing with validation
_BASE_DIR = Path(__file__).resolve().parent

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
	raise RuntimeError("DISCORD_TOKEN environment variable is required")

_GUILD_ID = os.getenv("GUILD_ID")
if not _GUILD_ID:
	raise RuntimeError("GUILD_ID environment variable is required")
try:
	GUILD_ID = int(_GUILD_ID)
except ValueError:
	raise RuntimeError("GUILD_ID must be an integer")

_TARGET_CHANNELS = os.getenv("TARGET_CHANNELS")
if not _TARGET_CHANNELS:
	raise RuntimeError("TARGET_CHANNELS environment variable is required (comma-separated IDs)")
try:
	TARGET_CHANNELS = [int(x.strip()) for x in _TARGET_CHANNELS.split(",") if x.strip()]
except ValueError:
	raise RuntimeError("TARGET_CHANNELS must be a comma-separated list of integers")

# Operational settings (allow overrides via env)
DAYS_OLD = int(os.getenv("DAYS_OLD", "7"))
if DAYS_OLD <= 0:
	raise ValueError("DAYS_OLD must be a positive integer")

CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "12"))
if CHECK_INTERVAL_HOURS <= 0:
	raise ValueError("CHECK_INTERVAL_HOURS must be a positive integer")

ARCHIVE_FOLDER = os.getenv("ARCHIVE_FOLDER")
if ARCHIVE_FOLDER:
	ARCHIVE_FOLDER = str(Path(ARCHIVE_FOLDER).resolve())
else:
	ARCHIVE_FOLDER = str((_BASE_DIR / "archive").resolve())

DATABASE_FILE = os.getenv("DATABASE_FILE") or str((_BASE_DIR / "image_tracker.db").resolve())

# Test mode: if True, bot does not delete messages (safe default).
# Set TEST_MODE=false (or DISABLE_TEST_MODE=true) to enable real deletions.
if _get_bool_env("DISABLE_TEST_MODE", default=False):
	TEST_MODE = False
else:
	TEST_MODE = _get_bool_env("TEST_MODE", default=True)

# Maximum archive size in megabytes. 0 means no limit.
MAX_ARCHIVE_SIZE_MB = int(os.getenv("MAX_ARCHIVE_SIZE_MB", "0"))

LOG_FILE = os.getenv("LOG_FILE")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "5242880"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# File type management
FILE_TYPES = MANAGED_EXTENSIONS

