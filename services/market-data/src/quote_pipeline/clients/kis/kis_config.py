"""KIS API 설정 및 상수."""

from dataclasses import dataclass
from enum import Enum


class KisTrId(str, Enum):
    """KIS WebSocket TR_ID 상수."""

    # 국내주식
    DOMESTIC_TICK = "H0UNCNT0"  # 국내주식 실시간체결가(통합)

    # 해외주식
    OVERSEAS_TICK = "HDFSCNT0"  # 해외주식 실시간체결가


class KisTrType(str, Enum):
    """KIS WebSocket TR_TYPE 상수."""

    REGISTER = "1"  # 등록
    UNREGISTER = "2"  # 해제


@dataclass(frozen=True)
class KisSubscription:
    """KIS 구독 정보."""

    tr_id: str
    tr_key: str
    symbol: str

    @classmethod
    def for_domestic(cls, symbol: str) -> "KisSubscription":
        """국내주식 구독 정보 생성."""
        return cls(
            tr_id=KisTrId.DOMESTIC_TICK.value,
            tr_key=symbol,
            symbol=symbol,
        )

    @classmethod
    def for_overseas(cls, symbol: str, exchange: str) -> "KisSubscription":
        """
        해외주식 구독 정보 생성.

        Args:
            symbol: 종목 코드 (예: NVDA, AAPL)
            exchange: 거래소 코드 (예: NAS, NYS)

        Returns:
            KisSubscription 인스턴스
        """
        tr_key = f"D{exchange}{symbol}"
        return cls(
            tr_id=KisTrId.OVERSEAS_TICK.value,
            tr_key=tr_key,
            symbol=symbol,
        )


def build_subscription(symbol: str, market: str, exchange: str = "NAS") -> KisSubscription:
    """
    심볼과 마켓 정보로 구독 정보를 생성합니다.

    Args:
        symbol: 종목 코드
        market: 마켓 코드 ("KR" 또는 기타)
        exchange: 해외주식의 경우 거래소 코드 (기본: NAS)

    Returns:
        KisSubscription 인스턴스
    """
    if market == "KR":
        return KisSubscription.for_domestic(symbol)
    return KisSubscription.for_overseas(symbol, exchange)


def get_ws_endpoint(tr_id: str) -> str:
    """
    TR_ID에 해당하는 WebSocket 엔드포인트 경로를 반환합니다.

    Args:
        tr_id: KIS TR_ID

    Returns:
        WebSocket 엔드포인트 경로 (예: /tryitout/H0UNCNT0)
    """
    return f"/tryitout/{tr_id}"


@dataclass
class KisConfig:
    app_key: str
    app_secret: str          # tokenP, REST에서 사용하는 appsecret
    is_vts: bool = False     # 모의투자 여부

    @property
    def base_url(self) -> str:
        # REST base url
        if self.is_vts:
            return "https://openapivts.koreainvestment.com:29443"
        return "https://openapi.koreainvestment.com:9443"

    @property
    def ws_base_url(self) -> str:
        # WebSocket base url (다중연결: 도메인 직접 사용)
        if self.is_vts:
            return "ws://ops.koreainvestment.com:31000"  # 모의계좌
        return "ws://ops.koreainvestment.com:21000"  # 실전계좌
