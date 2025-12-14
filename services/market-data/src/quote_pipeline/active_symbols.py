import asyncio
import contextlib
import logging
from typing import Optional, Set

from quote_pipeline.config import Provider, Settings
from quote_pipeline.sinks import Sink

logger = logging.getLogger(__name__)


async def fetch_active_symbols(redis_client, set_name: str) -> Set[str]:
    raw = await redis_client.smembers(set_name)
    return set(raw or [])


async def resolve_provider(symbol: str, db, fallback_only: bool = False) -> Optional[str]:
    """
    종목 → provider 매핑.
    1) securities_master 조회
    2) 패턴 매칭 (Upbit/Binance)
    """
    provider: Optional[str] = None

    # 1) DB 조회
    if db and not fallback_only:
        try:
            row = await db.fetchrow(
                "SELECT national, market FROM securities_master WHERE symbol = $1 LIMIT 1",
                symbol,
            )
            if row:
                national = (row["national"] or "").upper()
                market = (row["market"] or "").upper()
                if national == "KR":
                    provider = Provider.kis_new.value
                elif national == "US":
                    provider = Provider.kis_new.value
                elif market in ("KOSPI", "KOSDAQ"):
                    provider = Provider.kis_new.value
        except Exception as exc:
            logger.warning("provider resolve via DB failed for %s: %s", symbol, exc)

    # 2) 패턴 매칭 (fallback)
    if provider is None:
        sym_low = symbol.lower()
        if sym_low.startswith("krw-"):
            provider = Provider.upbit.value
        elif sym_low.endswith("usdt"):
            provider = Provider.binance.value

    return provider


async def filter_symbols_for_provider(redis_client, provider: Provider, base_set: str, provider_set: str):
    """공용 set + provider 전용 set을 합쳐서 현재 provider가 처리해야 할 심볼만 반환."""
    # provider 전용 set
    direct = await fetch_active_symbols(redis_client, provider_set)

    # 공용 set (provider 미지정) → DB/패턴으로 필터링
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


async def manage_dynamic_ingestor(settings: Settings, sink: Sink) -> None:
    """active_symbols Set을 주기적으로 폴링해 구독 심볼을 동적으로 반영한다."""
    try:
        import redis.asyncio as redis  # type: ignore
    except ImportError as exc:
        raise RuntimeError("redis package not installed for dynamic mode") from exc

    if not settings.redis.url:
        raise RuntimeError("dynamic mode requires REDIS_URL")

    redis_client = redis.from_url(settings.redis.url, decode_responses=True)

    base_set = settings.dynamic.active_set
    provider_set = f"{base_set}:{settings.provider.value}"

    # 초기 심볼을 provider 전용 set에 seed
    if settings.symbols:
        await redis_client.sadd(provider_set, *settings.symbols)

    async def start_ingestor(symbols):
        from quote_pipeline.pipeline import build_ingestor

        updated_settings = settings.copy()
        updated_settings.symbols = list(symbols)
        ingestor = build_ingestor(updated_settings, sink)
        task = asyncio.create_task(ingestor.run_forever())
        return task, ingestor

    current_symbols: Set[str] = set()
    task: asyncio.Task | None = None
    ingestor = None

    try:
        current_symbols = await filter_symbols_for_provider(
            redis_client, settings.provider, base_set, provider_set
        )
        if current_symbols:
            task, ingestor = await start_ingestor(current_symbols)

        while True:
            await asyncio.sleep(settings.dynamic.poll_interval_s)
            new_symbols = await filter_symbols_for_provider(
                redis_client, settings.provider, base_set, provider_set
            )
            if new_symbols != current_symbols:
                logger.info(
                    "Active symbols changed (%s): %s -> %s",
                    settings.provider.value,
                    current_symbols,
                    new_symbols,
                )
                current_symbols = new_symbols 
                # ingestor 에서 apply_symbols 메서드 제공 시 심볼만 갱신 (kis ingestor)
                if ingestor and hasattr(ingestor, "apply_symbols"):
                    # FIXME : ingestor 타입 해결 필요 (active_symbols 에서 ingestor 를 호출하는 패턴이 안좋은 것 같음)
                    await ingestor.apply_symbols(current_symbols)  # type: ignore[func-returns-value]
                # 그렇지 않으면 ingestor 재시작 (upbit, binance ingestor)
                else:
                    if task:
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task
                    task, ingestor = await start_ingestor(current_symbols)
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        # 종료 시 provider set 초기화(공용 set은 유지)
        await redis_client.delete(provider_set)
