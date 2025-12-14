import logging
from typing import Optional

from quote_pipeline.config import Provider
from quote_pipeline.db import get_db

logger = logging.getLogger(__name__)


async def resolve_provider(symbol: str, db=None) -> Provider:
    """
    심볼을 DB 조회하여 적절한 provider 반환.

    1. securities_master DB 조회 → national 기반 판단
    2. DB에 없으면 패턴 매칭 폴백
    3. 기본값: kis
    """
    # 1. 패턴 매칭 우선 (DB 조회 없이 빠르게 판단 가능한 경우)
    if symbol.startswith("KRW-"):
        return Provider.upbit

    symbol_lower = symbol.lower()
    if symbol_lower.endswith("usdt") or symbol_lower.endswith("btc"):
        return Provider.binance

    # 2. DB 조회
    if db is None:
        db = get_db()

    try:
        await db.connect()
        row = await db.fetchrow(
            "SELECT national, market FROM securities_master WHERE symbol = $1",
            symbol,
        )

        if row:
            national = row["national"]
            # 한국/미국/일본/중국/홍콩/베트남 → kis
            if national in ("KR", "US", "JP", "CN", "HK", "VN"):
                logger.debug("[symbol_resolver] %s → kis (DB: national=%s)", symbol, national)
                return Provider.kis

    except Exception as e:
        logger.warning("[symbol_resolver] DB 조회 실패 (symbol=%s): %s", symbol, e)

    # 3. 기본값
    logger.debug("[symbol_resolver] %s → kis (default)", symbol)
    return Provider.kis


async def classify_symbols_by_provider(
    symbols: list[str],
) -> dict[Provider, set[str]]:
    """
    심볼 목록을 provider별로 분류.

    Returns:
        {Provider.kis: {"NVDA", "005930"}, Provider.upbit: {"KRW-BTC"}, ...}
    """
    result: dict[Provider, set[str]] = {p: set() for p in Provider}

    db = get_db()
    try:
        await db.connect()

        for symbol in symbols:
            provider = await resolve_provider(symbol, db)
            result[provider].add(symbol)
            logger.info("[symbol_resolver] %s → %s", symbol, provider.value)

    finally:
        await db.close()

    # 빈 set 제거
    return {k: v for k, v in result.items() if v}
