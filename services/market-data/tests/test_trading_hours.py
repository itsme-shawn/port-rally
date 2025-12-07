from types import SimpleNamespace

import pytest

from quote_pipeline.utils.trading_hours import infer_market_from_symbol, is_market_open


def test_infer_market_from_symbol():
    # 6자리 숫자는 국내(KR), 그 외는 해외(US)로 판정
    assert infer_market_from_symbol("005930") == "KR"
    assert infer_market_from_symbol("NVDA") == "US"
    assert infer_market_from_symbol("AAPL") == "US"


@pytest.mark.parametrize(
    "open_kst, close_kst, now_utc, expected",
    [
        ("09:00:00", "15:30:00", "2025-01-01T03:00:00+00:00", True),   # 12:00 KST (장중)
        ("22:30:00", "05:00:00", "2025-01-01T13:00:00+00:00", False),  # 22:00 KST (개장 전)
        ("22:30:00", "05:00:00", "2025-01-01T14:00:00+00:00", True),   # 23:00 KST (개장 후)
    ],
)
def test_is_market_open_cross_midnight(open_kst, close_kst, now_utc, expected):
    # 자정 교차 구간(예: 22:30~05:00) 포함 장 운영 시간 판정
    hours_obj = SimpleNamespace(open_kst=open_kst, close_kst=close_kst)
    import datetime

    now_dt = datetime.datetime.fromisoformat(now_utc)
    result = is_market_open(lambda: hours_obj, now_utc=now_dt)
    assert result == expected
