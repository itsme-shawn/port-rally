import logging
import os
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(log_level)
    if not root.handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    else:
        for handler in root.handlers:
            handler.setLevel(log_level)
