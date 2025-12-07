import logging
from datetime import datetime, time, timedelta
from typing import Callable

logger = logging.getLogger(__name__)


def is_market_open(
    fetch_hours: Callable[[], object],
    open_attr: str = "open_kst",
    close_attr: str = "close_kst",
    tz_offset_hours: int = 9,  # KST 기준 (UTC+9)
) -> bool:
    """
    장 운영 시간 오픈 여부 체크 공용 함수.
    - fetch_hours: open/close 속성이 있는 객체를 반환하는 콜러블 (예: kis.trading_hours("US"))
    - open_attr/close_attr: open/close 시간 속성명 (기본 open_kst/close_kst)
    - tz_offset_hours: UTC에서 대상 시간대로의 오프셋 (기본 KST = +9)
    """
    hours = fetch_hours()
    open_str = getattr(hours, open_attr, None)
    close_str = getattr(hours, close_attr, None)
    if not open_str or not close_str:
        raise ValueError("Missing trading hours data")

    open_t = time.fromisoformat(str(open_str))
    close_t = time.fromisoformat(str(close_str))
    now_local = datetime.utcnow() + timedelta(hours=tz_offset_hours)
    now_t = now_local.time()

    if open_t <= close_t:
        return open_t <= now_t <= close_t
    # Crossing midnight (e.g., 22:30~05:00)
    return now_t >= open_t or now_t <= close_t


def infer_market_from_symbol(symbol: str) -> str:
    """
    심볼로 시장을 추정.
    - 6자리 숫자: KR
    - 그 외: US (기본)
    """
    if len(symbol) == 6 and symbol.isdigit():
        return "KR"
    return "US"
