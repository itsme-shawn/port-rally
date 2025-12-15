"""
Ingestor 관리 모듈.

4가지 실행 모드 조합:
- single_static: 단일 provider, 고정 심볼
- single_dynamic: 단일 provider, Redis active_symbols 기반 동적 심볼
- multi_static: 다중 provider, 고정 심볼
- multi_dynamic: 다중 provider, Redis active_symbols 기반 동적 심볼
"""

import asyncio
import contextlib
import logging
from typing import Set

from quote_pipeline.config import Provider, Settings
from quote_pipeline.pipeline import build_ingestor, build_store
from quote_pipeline.sinks import Sink

logger = logging.getLogger(__name__)


# =============================================================================
# Static Mode (고정 심볼)
# =============================================================================


async def run_single_provider_static_symbol(settings: Settings, sink: Sink) -> None:
    """
    단일 provider, 고정 심볼 모드.
    가장 기본적인 형태: 설정된 심볼로 단일 ingestor 실행.
    """
    if not settings.providers:
        raise ValueError("No provider specified")

    provider = settings.providers[0]
    logger.info("[single_static] Starting provider=%s symbols=%s", provider.value, settings.symbols)

    ingestor = build_ingestor(settings, provider, sink)
    await ingestor.run_forever()


async def run_multi_provider_static_symbol(settings: Settings, sink: Sink) -> None:
    """
    다중 provider, 고정 심볼 모드.
    여러 provider를 asyncio.gather로 병렬 실행.
    심볼은 시작 시 provider별로 분류됨.
    """
    if not settings.providers:
        raise ValueError("No providers specified")

    # 심볼을 provider별로 분류
    from quote_pipeline.ingestors.helper.symbol_resolver import classify_symbols_by_provider

    classified = await classify_symbols_by_provider(settings.symbols)

    tasks = []
    for provider in settings.providers:
        provider_symbols = classified.get(provider, set())
        if not provider_symbols:
            logger.warning("[multi_static] No symbols for provider=%s, skipping", provider.value)
            continue

        # provider별 settings 생성 (symbols만 변경)
        provider_settings = settings.model_copy()
        provider_settings.symbols = list(provider_symbols)

        ingestor = build_ingestor(provider_settings, provider, sink)
        task = asyncio.create_task(ingestor.run_forever())
        tasks.append(task)
        logger.info("[multi_static] Started provider=%s symbols=%s", provider.value, provider_symbols)

    if not tasks:
        raise ValueError("No ingestors started - no symbols matched any provider")

    await asyncio.gather(*tasks)


# =============================================================================
# Dynamic Mode (Redis active_symbols 기반)
# =============================================================================


async def run_single_provider_dynamic_symbol(settings: Settings, sink: Sink, redis_client) -> None:
    """
    단일 provider, 동적 심볼 모드.
    Redis active_symbols:{provider} Set을 폴링하여 심볼 변경 감지.
    """
    if not settings.providers:
        raise ValueError("No provider specified")

    provider = settings.providers[0]
    await _run_dynamic_symbol_loop(settings, provider, sink, redis_client)


async def run_multi_provider_dynamic_symbol(settings: Settings, sink: Sink, redis_client) -> None:
    """
    다중 provider, 동적 심볼 모드.
    각 provider별로 Redis active_symbols:{provider} Set을 폴링.
    """
    if not settings.providers:
        raise ValueError("No providers specified")

    tasks = []
    for provider in settings.providers:
        task = asyncio.create_task(
            _run_dynamic_symbol_loop(settings, provider, sink, redis_client)
        )
        tasks.append(task)
        logger.info("[multi_dynamic] Started dynamic loop for provider=%s", provider.value)

    await asyncio.gather(*tasks)


async def _run_dynamic_symbol_loop(
    settings: Settings, provider: Provider, sink: Sink, redis_client
) -> None:
    """
    단일 provider의 동적 구독 루프 (내부 헬퍼).
    Redis Set을 폴링하여 심볼 변경 시 ingestor에 반영.
    """
    from quote_pipeline.ingestors.helper.active_symbols_store import filter_symbols_for_provider

    base_set = settings.dynamic.active_set
    provider_set = f"{base_set}:{provider.value}"

    async def start_ingestor(symbols: Set[str]):
        provider_settings = settings.model_copy()
        provider_settings.symbols = list(symbols)
        ingestor = build_ingestor(provider_settings, provider, sink)
        task = asyncio.create_task(ingestor.run_forever())
        return task, ingestor

    current_symbols: Set[str] = set()
    task: asyncio.Task | None = None
    ingestor = None

    try:
        # 초기 심볼 로드
        current_symbols = await filter_symbols_for_provider(
            redis_client, provider, base_set, provider_set
        )
        logger.info("[%s] Initial symbols: %s", provider.value, current_symbols)

        if current_symbols:
            task, ingestor = await start_ingestor(current_symbols)

        # 폴링 루프
        while True:
            await asyncio.sleep(settings.dynamic.poll_interval_s)
            new_symbols = await filter_symbols_for_provider(
                redis_client, provider, base_set, provider_set
            )

            if new_symbols != current_symbols:
                logger.info(
                    "[%s] Active symbols changed: %s -> %s",
                    provider.value,
                    current_symbols,
                    new_symbols,
                )
                current_symbols = new_symbols

                # ingestor가 apply_symbols 지원하면 웹소켓 유지하며 심볼만 변경
                if ingestor and hasattr(ingestor, "apply_symbols"):
                    await ingestor.apply_symbols(current_symbols)  # type: ignore
                # 그 외에는 ingestor 재시작
                else:
                    if task:
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task
                    if current_symbols:
                        task, ingestor = await start_ingestor(current_symbols)
                    else:
                        task = None
                        ingestor = None
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        logger.info("[%s] Dynamic loop stopped", provider.value)


# =============================================================================
# 통합 진입점
# =============================================================================


async def run_ingestor(settings: Settings, sink: Sink, redis_client=None) -> None:
    """
    설정에 따라 적절한 실행 모드 선택.

    Args:
        settings: 파이프라인 설정
        sink: 출력 Sink
        redis_client: Redis 클라이언트 (동적 모드에서 필요)
    """
    is_multi = len(settings.providers) > 1
    is_dynamic = settings.dynamic.enabled

    if is_dynamic and redis_client is None:
        raise ValueError("redis_client required for dynamic mode")

    # QuoteStore 생성 및 실행 (Redis URL 설정 시)
    store = build_store(settings)
    store_task = None
    if store:
        store_task = asyncio.create_task(store.start())
        logger.info("QuoteStore started as background task")

    try:
        if is_multi:
            if is_dynamic:
                logger.info("Running in multi_dynamic mode")
                await run_multi_provider_dynamic_symbol(settings, sink, redis_client)
            else:
                logger.info("Running in multi_static mode")
                await run_multi_provider_static_symbol(settings, sink)
        else:
            if is_dynamic:
                logger.info("Running in single_dynamic mode")
                await run_single_provider_dynamic_symbol(settings, sink, redis_client)
            else:
                logger.info("Running in single_static mode")
                await run_single_provider_static_symbol(settings, sink)
    finally:
        # QuoteStore 정리
        if store_task:
            store_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await store_task
            await store.stop()
            logger.info("QuoteStore stopped")
