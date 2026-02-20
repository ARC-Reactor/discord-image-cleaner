import os
import importlib
from pathlib import Path


def test_setup_logging(tmp_path):
    log_file = str(tmp_path / "logs" / "app.log")
    from logging_config import setup_logging

    # ensure no handlers present
    import logging
    for h in list(logging.getLogger().handlers):
        logging.getLogger().removeHandler(h)

    setup_logging(log_file, max_bytes=1024, backup_count=1)

    # emit a log message to create the file
    logging.getLogger(__name__).info("test message")

    assert Path(log_file).exists()
