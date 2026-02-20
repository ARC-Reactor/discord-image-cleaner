import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[str] = None, max_bytes: int = 5_242_880, backup_count: int = 5):
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    if log_file:
        p = Path(log_file)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(str(p), maxBytes=max_bytes, backupCount=backup_count)
        fh.setFormatter(fmt)
        root.addHandler(fh)

    # reduce verbosity for external libs
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
