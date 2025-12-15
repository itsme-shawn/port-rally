"""Unified quote DTO - 통합 시세 데이터 전송 객체."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class UniQuoteDto:
    """
    통합 시세 DTO.

    모든 provider(KIS, Upbit, Binance)의 시세 데이터가
    이 형식으로 정규화되어 시스템 내부에서 유통됩니다.
    """

    symbol: str
    """심볼 (예: NVDA, 005930, BTC)"""

    provider: str
    """데이터 제공자 (kis, upbit, binance)"""

    price: Optional[Decimal]
    """현재가"""

    timestamp: datetime
    """시세 발생 시각"""

    national: str = "US"
    """국가 코드 (KR, US, JP 등)"""

    market: str = "NAS"
    """시장 코드 (NAS, KRX, KOSPI, KOSDAQ 등)"""

    volume: Optional[Decimal] = None
    """거래량"""

    open: Optional[Decimal] = None
    """시가"""

    high: Optional[Decimal] = None
    """고가"""

    low: Optional[Decimal] = None
    """저가"""

    change: Optional[Decimal] = None
    """전일대비 (절대값)"""

    change_rate: Optional[Decimal] = None
    """등락률 (%)"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Provider별 추가 필드 (sign, bid/ask 등)"""

    def to_dict(self) -> Dict[str, Any]:
        """
        이벤트를 딕셔너리로 변환.

        Redis Pub/Sub 등 외부 시스템으로 전송 시 사용합니다.
        """
        return {
            "symbol": self.symbol,
            "provider": self.provider,
            "national": self.national,
            "market": self.market,
            "price": str(self.price) if self.price is not None else None,
            "timestamp": self.timestamp.isoformat(),
            "volume": str(self.volume) if self.volume is not None else None,
            "open": str(self.open) if self.open is not None else None,
            "high": str(self.high) if self.high is not None else None,
            "low": str(self.low) if self.low is not None else None,
            "change": str(self.change) if self.change is not None else None,
            "change_rate": str(self.change_rate) if self.change_rate is not None else None,
            "metadata": self.metadata,
        }
