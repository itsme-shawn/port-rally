"""Stdout publisher - 표준 출력 발행자."""

import json
from typing import Any, Dict

from quote_pipeline.publishers.base_publisher import BasePublisher


class StdoutPublisher(BasePublisher):
    """
    표준 출력 발행자.

    메시지를 stdout으로 출력합니다.
    """

    def __init__(self, indent: bool = False) -> None:
        """
        StdoutPublisher 초기화.

        Args:
            indent: JSON 들여쓰기 여부
        """
        self.indent = indent

    async def publish(self, payload: Dict[str, Any]) -> None:
        """
        표준 출력으로 메시지를 출력합니다.

        Args:
            payload: 출력할 데이터 (JSON 직렬화 가능)
        """
        msg = json.dumps(payload, ensure_ascii=False, indent=2 if self.indent else None)
        print(msg, flush=True)
