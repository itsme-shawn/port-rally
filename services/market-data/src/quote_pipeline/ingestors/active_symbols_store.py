import logging
from typing import Optional, Set

from quote_pipeline.config import Provider

logger = logging.getLogger(__name__)


async def fetch_active_symbols(redis_client, set_name: str) -> Set[str]:
    """Redis Set에서 심볼 집합을 조회."""
    raw = await redis_client.smembers(set_name)
    return set(raw or [])


async def resolve_provider(symbol: str, db, fallback_only: bool = False) -> Optional[str]:
    """
    심볼로 provider를 판별.
    1) securities_master 조회
    2) 실패 시 패턴 매칭 (KRW- → upbit, *usdt → binance)
    """
    provider: Optional[str] = None

    if db and not fallback_only:
        try:
            row = await db.fetchrow(
                "SELECT national, market FROM securities_master WHERE symbol = $1 LIMIT 1",
                symbol,
            )
            if row:
                national = (row["national"] or "").upper()
                market = (row["market"] or "").upper()
                if national in ("KR", "US") or market in ("KOSPI", "KOSDAQ"):
                    provider = Provider.kis_new.value
        except Exception as exc:
            logger.warning("provider resolve via DB failed for %s: %s", symbol, exc)

    if provider is None:
        sym_low = symbol.lower()
        if sym_low.startswith("krw-"):
            provider = Provider.upbit.value
        elif sym_low.endswith("usdt"):
            provider = Provider.binance.value

    return provider


async def filter_symbols_for_provider(redis_client, provider: Provider, base_set: str, provider_set: str):
    """
    공용 set + provider 전용 set을 합쳐 현재 provider가 처리할 심볼만 반환.
    """
    direct = await fetch_active_symbols(redis_client, provider_set)
    generic = await fetch_active_symbols(redis_client, base_set)

    matched: Set[str] = set(direct)

    db = None
    try:
        from quote_pipeline.db import get_db

        db = get_db()
        await db.connect()
    except Exception:
        db = None

    for sym in generic:
        prov = await resolve_provider(sym, db, fallback_only=not bool(db))
        if prov == provider.value:
            matched.add(sym)

    return matched
