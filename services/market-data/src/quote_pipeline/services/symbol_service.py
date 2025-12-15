"""Symbol service - 심볼 관리 서비스."""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SymbolService:
    """
    심볼 관리 서비스.

    심볼→마켓 매핑을 캐싱하고 DB 조회를 담당합니다.
    여러 ingestor에서 공유 가능합니다.
    """

    def __init__(self, db_pool=None):
        """
        SymbolService 초기화.

        Args:
            db_pool: 데이터베이스 연결 풀 (Optional)
        """
        self.db_pool = db_pool
        self._cache: Dict[str, Tuple[str, str]] = {}  # symbol → (market, national)

    async def load_kr_symbols(self) -> None:
        """
        DB에서 한국 심볼→마켓 매핑을 캐시에 로드합니다.

        기존 `KisIngestor._load_symbol_market_cache()` 로직을 추출.
        """
        if not self.db_pool:
            logger.warning("[SymbolService] DB pool not provided, skipping cache load")
            return

        try:
            from quote_pipeline.db import get_db

            db = get_db()
            rows = await db.fetch(
                "SELECT symbol, market FROM securities_master WHERE national = 'KR'"
            )
            for row in rows:
                self._cache[row["symbol"]] = (row["market"], "KR")

            logger.info("[SymbolService] Loaded %d KR symbols into cache", len(rows))
        except Exception:
            logger.warning("[SymbolService] Failed to load symbol cache from DB", exc_info=True)

    def get_market_info(self, symbol: str, default_market: str = "KRX") -> Tuple[str, str]:
        """
        심볼의 (market, national) 정보를 조회합니다.

        Args:
            symbol: 종목 심볼
            default_market: 캐시에 없을 경우 사용할 기본 마켓

        Returns:
            (market, national) 튜플
        """
        if symbol in self._cache:
            return self._cache[symbol]

        # 캐시에 없으면 기본값 반환
        return (default_market, "KR")

    def set_market_info(self, symbol: str, market: str, national: str) -> None:
        """
        심볼의 마켓 정보를 캐시에 저장합니다.

        Args:
            symbol: 종목 심볼
            market: 시장 코드 (KOSPI, KOSDAQ, NAS 등)
            national: 국가 코드 (KR, US 등)
        """
        self._cache[symbol] = (market, national)

    def clear_cache(self) -> None:
        """캐시를 초기화합니다."""
        self._cache.clear()
        logger.info("[SymbolService] Cache cleared")

    def get_cache_size(self) -> int:
        """캐시에 저장된 심볼 수를 반환합니다."""
        return len(self._cache)
