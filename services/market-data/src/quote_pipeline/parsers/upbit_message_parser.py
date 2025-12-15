"""Upbit message parser."""

import json
import logging
from typing import Any, List

from quote_pipeline.domain.upbit_quote_dto import UpbitQuoteDTO
from quote_pipeline.parsers.message_parser import MessageParser

logger = logging.getLogger(__name__)


class UpbitMessageParser(MessageParser):
    """Upbit raw JSON → UpbitQuoteDTO 변환."""

    def parse(self, raw_message: str) -> List[Any]:
        try:
            obj = json.loads(raw_message)
        except json.JSONDecodeError as exc:
            logger.warning("[UpbitParser] JSON decode error: %s", exc)
            return []

        # Upbit는 단일 JSON 오브젝트를 보낸다.
        if not isinstance(obj, dict):
            logger.debug("[UpbitParser] Unexpected payload type: %s", type(obj))
            return []

        dto = UpbitQuoteDTO(
            code=obj.get("code", ""),
            type=obj.get("type", ""),
            trade_price=obj.get("trade_price"),
            trade_volume=obj.get("trade_volume"),
            timestamp=obj.get("timestamp"),
            trade_timestamp=obj.get("trade_timestamp"),
            signed_change_price=obj.get("signed_change_price"),
            signed_change_rate=obj.get("signed_change_rate"),
            high_price=obj.get("high_price"),
            low_price=obj.get("low_price"),
            opening_price=obj.get("opening_price"),
        )
        return [dto]
