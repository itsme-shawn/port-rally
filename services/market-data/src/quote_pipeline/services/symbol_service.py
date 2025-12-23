"""Symbol service - 심볼 메타데이터 관리 서비스."""

import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SymbolMetadata:
    """심볼 메타데이터."""

    symbol: str
    national: str  # KR, US, HK 등
    exchange: str  # KOSPI, KOSDAQ, NAS, NYS, AMS, HKS 등


class SymbolNotFoundError(Exception):
    """심볼을 찾을 수 없을 때 발생하는 예외."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Symbol '{symbol}' not found in cache")


class MultipleSymbolsFoundError(Exception):
    """동일한 심볼이 여러 개 발견되었을 때 발생하는 예외."""

    def __init__(self, symbol: str, count: int):
        self.symbol = symbol
        self.count = count
        super().__init__(f"Symbol '{symbol}' found {count} times in cache (expected 1)")


class SymbolService:
    """
    심볼 메타데이터 관리 서비스.

    DB에서 (symbol, national, exchange) 정보를 메모리에 캐시하고,
    심볼 조회 API를 제공합니다.
    """

    def __init__(self, db_pool=None):
        """
        SymbolService 초기화.

        Args:
            db_pool: 데이터베이스 연결 풀 (Optional)
        """
        self.db_pool = db_pool
        # symbol → List[SymbolMetadata] (동일 심볼이 여러 국가에 있을 수 있음)
        self._cache: Dict[str, List[SymbolMetadata]] = {}

    async def load_all_symbols(self) -> int:
        """
        DB에서 모든 심볼 메타데이터를 메모리에 로드합니다.

        Returns:
            로드된 심볼 개수
        """
        if not self.db_pool:
            logger.warning("[SymbolService] DB pool not provided, skipping cache load")
            return 0

        try:
            from quote_pipeline.db import get_db

            db = get_db()
            rows = await db.fetch(
                "SELECT symbol, national, market AS exchange FROM securities_master ORDER BY symbol"
            )

            self._cache.clear()
            for row in rows:
                metadata = SymbolMetadata(
                    symbol=row["symbol"],
                    national=row["national"],
                    exchange=row["exchange"],
                )
                if metadata.symbol not in self._cache:
                    self._cache[metadata.symbol] = []
                self._cache[metadata.symbol].append(metadata)

            total_count = len(rows)
            unique_count = len(self._cache)
            logger.info(
                "[SymbolService] Loaded %d symbols (%d unique) into cache",
                total_count,
                unique_count,
            )
            return total_count

        except Exception:
            logger.error("[SymbolService] Failed to load symbols from DB", exc_info=True)
            return 0

    async def load_symbols_by_national(self, national: str) -> int:
        """
        특정 국가의 심볼만 메모리에 로드합니다.

        Args:
            national: 국가 코드 (KR, US, HK 등)

        Returns:
            로드된 심볼 개수
        """
        if not self.db_pool:
            logger.warning("[SymbolService] DB pool not provided, skipping cache load")
            return 0

        try:
            from quote_pipeline.db import get_db

            db = get_db()
            rows = await db.fetch(
                "SELECT symbol, national, market AS exchange FROM securities_master WHERE national = $1 ORDER BY symbol",
                national,
            )

            # 기존 캐시에서 해당 national만 제거
            symbols_to_remove = [
                symbol
                for symbol, metadatas in self._cache.items()
                if any(m.national == national for m in metadatas)
            ]
            for symbol in symbols_to_remove:
                self._cache[symbol] = [
                    m for m in self._cache[symbol] if m.national != national
                ]
                if not self._cache[symbol]:
                    del self._cache[symbol]

            # 새로운 데이터 추가
            for row in rows:
                metadata = SymbolMetadata(
                    symbol=row["symbol"],
                    national=row["national"],
                    exchange=row["exchange"],
                )
                if metadata.symbol not in self._cache:
                    self._cache[metadata.symbol] = []
                self._cache[metadata.symbol].append(metadata)

            count = len(rows)
            logger.info("[SymbolService] Loaded %d symbols (national=%s) into cache", count, national)
            return count

        except Exception:
            logger.error(
                "[SymbolService] Failed to load symbols (national=%s) from DB",
                national,
                exc_info=True,
            )
            return 0

    def get_metadata_by_symbol(self, symbol: str) -> SymbolMetadata:
        """
        심볼의 메타데이터를 조회합니다.

        Args:
            symbol: 종목 심볼

        Returns:
            SymbolMetadata 객체

        Raises:
            SymbolNotFoundError: 심볼을 찾을 수 없을 때
            MultipleSymbolsFoundError: 동일 심볼이 여러 개 있을 때
        """
        if symbol not in self._cache:
            raise SymbolNotFoundError(symbol)

        metadatas = self._cache[symbol]

        if len(metadatas) == 0:
            raise SymbolNotFoundError(symbol)

        if len(metadatas) > 1:
            raise MultipleSymbolsFoundError(symbol, len(metadatas))

        return metadatas[0]

    def get_all_metadata_by_symbol(self, symbol: str) -> List[SymbolMetadata]:
        """
        심볼의 모든 메타데이터를 조회합니다 (동일 심볼이 여러 국가에 있을 수 있음).

        Args:
            symbol: 종목 심볼

        Returns:
            SymbolMetadata 리스트

        Raises:
            SymbolNotFoundError: 심볼을 찾을 수 없을 때
        """
        if symbol not in self._cache:
            raise SymbolNotFoundError(symbol)

        return self._cache[symbol]

    def set_metadata(self, metadata: SymbolMetadata) -> None:
        """
        심볼 메타데이터를 캐시에 저장합니다.

        Args:
            metadata: SymbolMetadata 객체
        """
        if metadata.symbol not in self._cache:
            self._cache[metadata.symbol] = []

        # 동일한 (symbol, national) 조합이 있으면 제거
        self._cache[metadata.symbol] = [
            m
            for m in self._cache[metadata.symbol]
            if not (m.symbol == metadata.symbol and m.national == metadata.national)
        ]

        self._cache[metadata.symbol].append(metadata)

    def clear_cache(self) -> None:
        """캐시를 초기화합니다."""
        self._cache.clear()
        logger.info("[SymbolService] Cache cleared")

    def get_cache_size(self) -> int:
        """캐시에 저장된 고유 심볼 수를 반환합니다."""
        return len(self._cache)

    def get_total_count(self) -> int:
        """캐시에 저장된 전체 메타데이터 개수를 반환합니다."""
        return sum(len(metadatas) for metadatas in self._cache.values())

    def get_all_symbols(self) -> List[str]:
        """캐시에 저장된 모든 심볼을 반환합니다."""
        return sorted(self._cache.keys())

    def get_symbols_by_national(self, national: str) -> List[str]:
        """특정 국가의 심볼만 반환합니다."""
        symbols = set()
        for symbol, metadatas in self._cache.items():
            if any(m.national == national for m in metadatas):
                symbols.add(symbol)
        return sorted(symbols)
