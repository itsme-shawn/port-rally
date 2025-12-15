"""Upbit quote DTO - Upbit 실시간 시세 DTO."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UpbitQuoteDTO:
    """
    Upbit 실시간 시세 DTO.

    ticker 또는 trade 채널 데이터를 담습니다.
    """

    code: str  # 심볼 (예: KRW-BTC)
    type: str  # ticker, trade, orderbook 등
    trade_price: Optional[float] = None
    trade_volume: Optional[float] = None
    timestamp: Optional[int] = None
    trade_timestamp: Optional[int] = None
    signed_change_price: Optional[float] = None
    signed_change_rate: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    opening_price: Optional[float] = None
