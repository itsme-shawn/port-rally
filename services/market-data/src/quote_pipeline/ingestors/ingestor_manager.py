"""Ingestor manager - Ingestor 실행 모드 관리."""

import asyncio
import logging
from typing import Set

from quote_pipeline.config import Provider, Settings
from quote_pipeline.ingestors.ingestor_factory import IngestorFactory
from quote_pipeline.ingestors.base_ingestor import BaseIngestor
from quote_pipeline.publishers.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class IngestorManager:
    """
    Ingestor 실행 모드 관리자.

    4가지 실행 모드를 제공합니다:
    1. single_static: 단일 provider, 고정 심볼
    2. single_dynamic: 단일 provider, 동적 심볼 (Redis)
    3. multi_static: 다중 provider, 고정 심볼
    4. multi_dynamic: 다중 provider, 동적 심볼 (Redis)

    기존 manage_ingestor.py의 로직을 클래스로 재구성했습니다.
    """

    def __init__(self, settings: Settings, publisher: BasePublisher, db_pool=None, redis_client=None):
        """
        IngestorManager 초기화.

        Args:
            settings: 파이프라인 설정
            publisher: 출력 publisher
            db_pool: 데이터베이스 연결 풀 (Optional)
            redis_client: Redis 클라이언트 (동적 모드에 필요)
        """
        self.settings = settings
        self.publisher = publisher
        self.db_pool = db_pool
        self.redis_client = redis_client

    async def run_single_provider_static_symbol(self) -> None:
        """
        단일 provider, 고정 심볼 모드.

        가장 기본적인 형태: 설정된 심볼로 단일 ingestor 실행.
        """
        if not self.settings.providers:
            raise ValueError("No provider specified")

        provider = self.settings.providers[0]
        logger.info(
            "[single_static] Starting provider=%s symbols=%s",
            provider.value,
            self.settings.symbols,
        )

        ingestor = IngestorFactory.create_ingestor(
            settings=self.settings,
            provider=provider,
            publisher=self.publisher,
            db_pool=self.db_pool,
        )

        await ingestor.run_forever()

    async def run_multi_provider_static_symbol(self) -> None:
        """
        다중 provider, 고정 심볼 모드.

        여러 provider를 asyncio.gather로 병렬 실행.
        심볼은 시작 시 provider별로 분류됩니다.
        """
        if not self.settings.providers:
            raise ValueError("No providers specified")

        # 심볼을 provider별로 분류 (단순 규칙 기반)
        classified = self._classify_symbols(self.settings.symbols)

        tasks = []
        for provider in self.settings.providers:
            provider_symbols = classified.get(provider, set())
            if not provider_symbols:
                logger.warning(
                    "[multi_static] No symbols for provider=%s, skipping", provider.value
                )
                continue

            # provider별 settings 생성 (symbols만 변경)
            provider_settings = self.settings.model_copy()
            provider_settings.symbols = list(provider_symbols)

            ingestor = IngestorFactory.create_ingestor(
                settings=provider_settings,
                provider=provider,
                publisher=self.publisher,
                db_pool=self.db_pool,
            )

            task = asyncio.create_task(ingestor.run_forever())
            tasks.append(task)
            logger.info(
                "[multi_static] Started provider=%s symbols=%s", provider.value, provider_symbols
            )

        if not tasks:
            raise ValueError("No ingestors started - no symbols matched any provider")

        await asyncio.gather(*tasks)

    async def run_single_provider_dynamic_symbol(self) -> None:
        """
        단일 provider, 동적 심볼 모드.

        Redis active_symbols:{provider} Set을 폴링하여 심볼 변경 감지.
        """
        if not self.redis_client:
            raise ValueError("Redis client is required for dynamic mode")

        if not self.settings.providers:
            raise ValueError("No provider specified")

        provider = self.settings.providers[0]
        await self._run_dynamic_symbol_loop(provider)

    async def run_multi_provider_dynamic_symbol(self) -> None:
        """
        다중 provider, 동적 심볼 모드.

        각 provider별로 Redis active_symbols:{provider} Set을 폴링.
        """
        if not self.redis_client:
            raise ValueError("Redis client is required for dynamic mode")

        if not self.settings.providers:
            raise ValueError("No providers specified")

        tasks = []
        for provider in self.settings.providers:
            task = asyncio.create_task(self._run_dynamic_symbol_loop(provider))
            tasks.append(task)
            logger.info("[multi_dynamic] Started dynamic loop for provider=%s", provider.value)

        await asyncio.gather(*tasks)

    async def _run_dynamic_symbol_loop(self, provider: Provider) -> None:
        """
        단일 provider의 동적 구독 루프 (내부 헬퍼).

        Redis Set을 폴링하여 심볼 변경 시 ingestor에 반영합니다.

        Args:
            provider: Provider 타입
        """
        async def start_ingestor(symbols: Set[str]) -> tuple[asyncio.Task, BaseIngestor]:
            provider_settings = self.settings.model_copy()
            provider_settings.symbols = list(symbols)

            ingestor = IngestorFactory.create_ingestor(
                settings=provider_settings,
                provider=provider,
                publisher=self.publisher,
                db_pool=self.db_pool,
            )

            task = asyncio.create_task(ingestor.run_forever())
            return task, ingestor

        current_symbols: Set[str] = set()
        task: asyncio.Task | None = None
        ingestor: BaseIngestor | None = None

        try:
            # 초기 심볼 로드
            current_symbols = await self._get_symbols_from_redis(provider)
            logger.info("[%s] Initial symbols: %s", provider.value, current_symbols)

            if current_symbols:
                task, ingestor = await start_ingestor(current_symbols)

            # 폴링 루프
            while True:
                await asyncio.sleep(self.settings.dynamic.poll_interval_s)

                # Redis에서 최신 심볼 조회
                new_symbols = await self._get_symbols_from_redis(provider)

                # 변경사항 있는지 확인
                if new_symbols == current_symbols:
                    continue

                logger.info(
                    "[%s] Symbols changed: %s → %s",
                    provider.value,
                    current_symbols,
                    new_symbols,
                )

                # ingestor에 apply_symbols 함수가있으면 동적 변경, 없으면 재시작
                if ingestor and hasattr(ingestor.client, "apply_symbols"):
                    logger.info("[%s] Applying symbols dynamically", provider.value)
                    await ingestor.apply_symbols(new_symbols)
                else:
                    logger.info("[%s] Restarting ingestor with new symbols", provider.value)
                    # 기존 ingestor 종료
                    if task:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

                    # 새 ingestor 시작
                    if new_symbols:
                        task, ingestor = await start_ingestor(new_symbols)
                    else:
                        task, ingestor = None, None

                current_symbols = new_symbols

        finally:
            # Cleanup
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    def _classify_symbols(self, symbols: list[str]) -> dict[Provider, set[str]]:
        """
        심볼을 provider별로 분류합니다 (단순 규칙 기반).

        Args:
            symbols: 분류할 심볼 리스트

        Returns:
            Provider별 심볼 집합 딕셔너리
        """
        classified = {provider: set() for provider in self.settings.providers}

        for symbol in symbols:
            sym_upper = symbol.upper()
            sym_lower = symbol.lower()

            if sym_upper.startswith("KRW-"):
                if Provider.upbit in classified:
                    # Upbit는 대문자 코드 사용
                    classified[Provider.upbit].add(sym_upper)
            elif sym_lower.endswith("usdt") or sym_lower.endswith("btc"):
                if Provider.binance in classified:
                    classified[Provider.binance].add(symbol)
            else:
                # 기본값: kis (미국 주식)
                if Provider.kis in classified:
                    classified[Provider.kis].add(symbol)

        return classified

    async def _get_symbols_from_redis(self, provider: Provider) -> set[str]:
        """
        Redis에서 해당 provider의 활성 심볼을 조회합니다.

        Args:
            provider: Provider 타입

        Returns:
            활성 심볼 집합
        """
        provider_set = f"{self.settings.dynamic.active_set}:{provider.value}"
        logger.debug("[IngestorManager] Fetching symbols from Redis set: %s", provider_set)
        symbols = await self.redis_client.smembers(provider_set)
        result = set(symbols) if symbols else set()
        logger.debug("[IngestorManager] Got %d symbols from %s: %s", len(result), provider_set, result)
        return result
