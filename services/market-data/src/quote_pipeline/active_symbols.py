import asyncio
import contextlib
import logging
from typing import Set

from quote_pipeline.config import Settings
from quote_pipeline.sinks import Sink

logger = logging.getLogger(__name__)


async def fetch_active_symbols(redis_client, set_name: str) -> Set[str]:
    raw = await redis_client.smembers(set_name)
    return set(raw or [])


async def manage_dynamic_ingestor(settings: Settings, sink: Sink) -> None:
    """active_symbols Set을 주기적으로 폴링해 구독 심볼을 동적으로 반영한다."""
    try:
        import redis.asyncio as redis  # type: ignore
    except ImportError as exc:
        raise RuntimeError("redis package not installed for dynamic mode") from exc

    if not settings.redis.url:
        raise RuntimeError("dynamic mode requires REDIS_URL")

    redis_client = redis.from_url(settings.redis.url, decode_responses=True)

    # 초기 심볼을 active_set에 seed (필요 시 redis 종료 시 휘발성)
    if settings.symbols:
        await redis_client.sadd(settings.dynamic.active_set, *settings.symbols)

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
        current_symbols = await fetch_active_symbols(redis_client, settings.dynamic.active_set)
        if current_symbols:
            task, ingestor = await start_ingestor(current_symbols)

        while True:
            await asyncio.sleep(settings.dynamic.poll_interval_s)
            new_symbols = await fetch_active_symbols(redis_client, settings.dynamic.active_set)
            if new_symbols != current_symbols:
                logger.info("Active symbols changed: %s -> %s", current_symbols, new_symbols)
                current_symbols = new_symbols 
                # ingestor 에서 apply_symbols 메서드 제공 시 심볼만 갱신 (kis ingestor)
                if ingestor and hasattr(ingestor, "apply_symbols"):
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
        # 종료 시 active_set 초기화(희망에 따라 유지하고 싶다면 주석 처리)
        await redis_client.delete(settings.dynamic.active_set)
