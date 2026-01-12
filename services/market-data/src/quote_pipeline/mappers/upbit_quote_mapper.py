"""Upbit → UniQuote 매퍼."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from quote_pipeline.domain.uni_quote_dto import UniQuoteDto
from quote_pipeline.domain.upbit_quote_dto import UpbitQuoteDTO
from quote_pipeline.mappers.base_mapper import BaseMapper


class UpbitQuoteMapper(BaseMapper):
    """UpbitQuoteDTO를 UniQuoteDto로 변환한다."""

    async def to_uni_quote(self, dto: Any) -> UniQuoteDto | None:
        if not isinstance(dto, UpbitQuoteDTO):
            return None

        ts_ms: Optional[int] = dto.trade_timestamp or dto.timestamp
        ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) if ts_ms else datetime.now(timezone.utc)

        return UniQuoteDto(
            symbol=dto.code,
            provider="upbit",
            price=Decimal(dto.trade_price) if dto.trade_price is not None else None,
            timestamp=ts,
            national="KR",
            exchange="UPBIT",
            volume=Decimal(dto.trade_volume) if dto.trade_volume is not None else None,
            open=Decimal(dto.opening_price) if dto.opening_price is not None else None,
            high=Decimal(dto.high_price) if dto.high_price is not None else None,
            low=Decimal(dto.low_price) if dto.low_price is not None else None,
            change=Decimal(dto.signed_change_price) if dto.signed_change_price is not None else None,
            change_rate=Decimal(dto.signed_change_rate) if dto.signed_change_rate is not None else None,
            metadata={"type": dto.type},
        )
