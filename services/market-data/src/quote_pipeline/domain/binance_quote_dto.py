"""Binance quote DTO - Binance 실시간 시세 DTO."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BinanceQuoteDTO:
    """
    Binance 실시간 시세 DTO.

    trade 또는 bookTicker 채널 데이터를 담습니다.
    """

    s: Optional[str] = None  # symbol (예: BTCUSDT)
    symbol: Optional[str] = None  # symbol (대체 필드)
    p: Optional[str] = None  # trade price
    c: Optional[str] = None  # best ask price (bookTicker)
    q: Optional[str] = None  # trade quantity
    Q: Optional[str] = None  # best ask quantity (bookTicker)
    T: Optional[int] = None  # trade time
    E: Optional[int] = None  # event time
    stream_type: Optional[str] = None  # trade, bookTicker 등
