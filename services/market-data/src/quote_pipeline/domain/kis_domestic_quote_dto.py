"""KIS domestic quote DTO - KIS 국내주식 실시간 체결가 데이터 전송 객체."""

from dataclasses import dataclass


@dataclass
class KisDomesticQuoteDTO:
    """
    KIS 국내주식 실시간 체결가 (H0STCNT0) raw data.

    TODO: 추후 실제 데이터 형식 확인 후 필드 추가
    """

    symbol: str
    """종목코드"""

    raw_data: str
    """원본 데이터 (파싱 전)"""
