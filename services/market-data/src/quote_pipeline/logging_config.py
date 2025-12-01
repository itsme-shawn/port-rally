import logging
import os
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
