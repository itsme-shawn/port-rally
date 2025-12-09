import logging
import os
from typing import Optional


def configure_logging(env_level: Optional[str] = None) -> None:
    """
    루트 로거 설정을 초기화/업데이트한다.
    필요한 경우 caller가 level 인자로 원하는 레벨을 직접 전달한다.
    """
    log_level = (env_level or "INFO").upper()

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

