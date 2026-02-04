"""Symbol service - TO-BE 구조 (symbol_map + symbol_detail) 사용."""

import logging
from dataclasses import dataclass, asdict, fields
from typing import Dict, List, Optional

from quote_pipeline.redis_meta import meta

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SymbolMetadata:
    """심볼 메타데이터."""

    symbol: str
    national: str  # KR, US, HK 등
    market: str  # KOSPI, KOSDAQ, NAS, NYS, AMS, HKS 등
    name_ko: Optional[str] = None
    name_en: Optional[str] = None
    asset_type: Optional[str] = "STOCK"
    currency: Optional[str] = None
    isin: Optional[str] = None
    asset_id: Optional[str] = None
    exchange: Optional[str] = None  # Backward compatibility

    @property
    def exchange_name(self) -> str:
        """Exchange name (alias for market)."""
        return self.market

    @classmethod
    def from_dict(cls, data: Dict) -> "SymbolMetadata":
        """딕셔너리에서 생성 (불필요한 필드 무시 및 호환성 처리)."""
        data = data.copy()

        # exchange -> market 매핑 (DB 쿼리에서 as exchange로 가져오는 경우 호환)
        if "exchange" in data and "market" not in data:
            data["market"] = data["exchange"]
        elif "market" in data and "exchange" not in data:
            data["exchange"] = data["market"]

        # 정의된 필드만 추출
        valid_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


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
    심볼 메타데이터 관리 서비스 (TO-BE 구조: symbol_map + symbol_detail).

    Redis 키 구조:
        symbol_map:{symbol} → Set of "national:market" (인덱스)
        symbol_detail:{national}:{market}:{symbol} → Hash (데이터)

        예:
        symbol_map:005930 → {"KR:KOSPI"}
        symbol_detail:KR:KOSPI:005930 → {asset_id, symbol, national, market, ...}
    """

    def __init__(self, db_pool=None, redis_client=None):
        """
        SymbolService 초기화.

        Args:
            db_pool: 데이터베이스 연결 풀 (Optional, load 시 필요)
            redis_client: Redis 클라이언트 (필수)
        """
        self.db_pool = db_pool
        self.redis_client = redis_client

    async def load_all_symbols(self) -> int:
        """
        DB에서 모든 심볼 메타데이터를 Redis에 로드합니다 (TO-BE 구조).

        Returns:
            로드된 심볼 개수
        """
        if not self.db_pool:
            logger.warning("[SymbolService] DB pool not provided, skipping load")
            return 0

        if not self.redis_client:
            logger.warning("[SymbolService] Redis client not provided, skipping load")
            return 0

        try:
            from quote_pipeline.db import get_db

            db = get_db()
            rows = await db.fetch(
                """
                SELECT
                    symbol, national, market, name_kr as name_ko, name_en,
                    'STOCK' as asset_type, currency, '' as isin, id::text as asset_id
                FROM assets_master
                ORDER BY symbol
                """
            )

            # 기존 Redis 캐시 삭제 (symbol_map:*, symbol_detail:* 키들)
            deleted_count = 0
            for pattern in ["symbol_map:*", "symbol_detail:*"]:
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        deleted_count += await self.redis_client.delete(*keys)
                    if cursor == 0:
                        break

            if deleted_count > 0:
                logger.info("[SymbolService] Cleared %d existing Redis keys", deleted_count)

            # Redis에 일괄 저장 (pipeline 사용)
            pipe = self.redis_client.pipeline()
            for row in rows:
                symbol = row["symbol"]
                national = row["national"]
                market = row["market"]

                # 1. symbol_map 인덱스 키
                map_key = meta.symbol_map(symbol=symbol)
                market_identifier = f"{national}:{market}"
                pipe.sadd(map_key.build(), market_identifier)

                # 2. symbol_detail 데이터 키
                detail_key = meta.symbol_detail(
                    national=national,
                    market=market,
                    symbol=symbol
                )
                metadata = {
                    "asset_id": str(row["asset_id"]),
                    "symbol": symbol,
                    "national": national,
                    "market": market,
                    "name_ko": row["name_ko"] or "",
                    "name_en": row["name_en"] or "",
                    "asset_type": row["asset_type"] or "",
                    "currency": row["currency"] or "",
                    "isin": row["isin"] or ""
                }
                pipe.hset(detail_key.build(), mapping=metadata)

            await pipe.execute()

            total_count = len(rows)
            logger.info("[SymbolService] Loaded %d symbols into Redis (TO-BE)", total_count)
            return total_count

        except Exception:
            logger.error("[SymbolService] Failed to load symbols from DB to Redis", exc_info=True)
            return 0

    async def get_metadata_by_symbol(
        self,
        symbol: str,
        national: Optional[str] = None,
        market: Optional[str] = None
    ) -> SymbolMetadata:
        """
        심볼의 메타데이터를 Redis에서 조회합니다 (TO-BE 구조).

        Args:
            symbol: 종목 심볼
            national: 국가 (Optional, 명시하면 빠른 조회)
            market: 시장 (Optional, national과 함께 사용)

        Returns:
            SymbolMetadata 객체

        Raises:
            SymbolNotFoundError: 심볼을 찾을 수 없을 때
            MultipleSymbolsFoundError: 동일 심볼이 여러 개 있을 때
        """
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        # 1. national + market 둘 다 있으면 직접 조회
        if national and market:
            detail_key = meta.symbol_detail(
                national=national,
                market=market,
                symbol=symbol
            )
            data = await self.redis_client.hgetall(detail_key.build())
            if data:
                return SymbolMetadata.from_dict(data)
            raise SymbolNotFoundError(symbol)

        # 2. symbol_map에서 시장 목록 조회
        map_key = meta.symbol_map(symbol=symbol)
        markets = await self.redis_client.smembers(map_key.build())

        if not markets:
            raise SymbolNotFoundError(symbol)

        if len(markets) > 1:
            raise MultipleSymbolsFoundError(symbol, len(markets))

        # 3. 첫 번째 시장의 데이터 조회
        market_identifier = list(markets)[0]  # "KR:KOSPI"
        nat, mkt = market_identifier.split(":")

        detail_key = meta.symbol_detail(
            national=nat,
            market=mkt,
            symbol=symbol
        )
        data = await self.redis_client.hgetall(detail_key.build())
        if data:
            return SymbolMetadata.from_dict(data)
        raise SymbolNotFoundError(symbol)

    async def get_all_metadata_by_symbol(self, symbol: str) -> List[SymbolMetadata]:
        """
        심볼의 모든 메타데이터를 Redis에서 조회합니다 (여러 시장).

        Args:
            symbol: 종목 심볼

        Returns:
            SymbolMetadata 리스트

        Raises:
            SymbolNotFoundError: 심볼을 찾을 수 없을 때
        """
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        # 1. symbol_map에서 시장 목록 조회
        map_key = meta.symbol_map(symbol=symbol)
        markets = await self.redis_client.smembers(map_key.build())

        if not markets:
            raise SymbolNotFoundError(symbol)

        # 2. 모든 시장의 데이터 조회
        results = []
        for market_identifier in markets:
            nat, mkt = market_identifier.split(":")
            detail_key = meta.symbol_detail(
                national=nat,
                market=mkt,
                symbol=symbol
            )
            data = await self.redis_client.hgetall(detail_key.build())
            if data:
                results.append(SymbolMetadata.from_dict(data))

        return results

    async def set_metadata(self, metadata: SymbolMetadata) -> None:
        """
        심볼 메타데이터를 Redis에 저장합니다 (TO-BE 구조).

        Args:
            metadata: SymbolMetadata 객체
        """
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        symbol = metadata.symbol
        national = metadata.national
        market = metadata.market

        # 1. symbol_map 업데이트
        map_key = meta.symbol_map(symbol=symbol)
        market_identifier = f"{national}:{market}"
        await self.redis_client.sadd(map_key.build(), market_identifier)

        # 2. symbol_detail 업데이트
        detail_key = meta.symbol_detail(
            national=national,
            market=market,
            symbol=symbol
        )
        data = {
            "asset_id": metadata.asset_id or "",
            "symbol": symbol,
            "national": national,
            "market": market,
            "name_ko": metadata.name_ko or "",
            "name_en": metadata.name_en or "",
            "asset_type": metadata.asset_type or "",
            "currency": metadata.currency or "",
            "isin": metadata.isin or ""
        }
        await self.redis_client.hset(detail_key.build(), mapping=data)

    async def clear_cache(self) -> None:
        """Redis 캐시를 초기화합니다 (TO-BE 구조)."""
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        deleted_count = 0
        for pattern in ["symbol_map:*", "symbol_detail:*"]:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
                if cursor == 0:
                    break

        logger.info("[SymbolService] Cleared %d Redis keys", deleted_count)

    async def get_cache_size(self) -> int:
        """Redis에 저장된 고유 심볼 수를 반환합니다."""
        if not self.redis_client:
            return 0

        pattern = "symbol_map:*"
        cursor = 0
        count = 0

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            count += len(keys)
            if cursor == 0:
                break

        return count

    async def get_total_count(self) -> int:
        """Redis에 저장된 전체 메타데이터 개수를 반환합니다."""
        if not self.redis_client:
            return 0

        pattern = "symbol_detail:*"
        cursor = 0
        count = 0

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            count += len(keys)
            if cursor == 0:
                break

        return count

    async def get_all_symbols(self) -> List[str]:
        """Redis에 저장된 모든 심볼을 반환합니다."""
        if not self.redis_client:
            return []

        pattern = "symbol_map:*"
        cursor = 0
        symbols = []

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                # key 형식: symbol_map:SYMBOL
                symbol = key.split(":", 1)[1] if ":" in key else key
                symbols.append(symbol)
            if cursor == 0:
                break

        return sorted(symbols)

    async def get_symbols_by_national(self, national: str) -> List[str]:
        """특정 국가의 심볼만 반환합니다."""
        if not self.redis_client:
            return []

        pattern = f"symbol_detail:{national}:*"
        cursor = 0
        symbols = set()

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                # key 형식: symbol_detail:KR:KOSPI:SYMBOL
                parts = key.split(":")
                if len(parts) >= 4:
                    symbol = parts[3]
                    symbols.add(symbol)
            if cursor == 0:
                break

        return sorted(list(symbols))

    async def get_statistics(self) -> Dict[str, int]:
        """
        Redis에 저장된 메타데이터 통계를 반환합니다.

        Returns:
            {
                "unique_symbols": int,
                "total_entries": int,
                "by_national": Dict[str, int]
            }
        """
        if not self.redis_client:
            return {"unique_symbols": 0, "total_entries": 0, "by_national": {}}

        unique_symbols = await self.get_cache_size()
        total_entries = await self.get_total_count()

        # national별 집계
        by_national = {}
        pattern = "symbol_detail:*"
        cursor = 0

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=1000)
            for key in keys:
                # key 형식: symbol_detail:KR:KOSPI:SYMBOL
                parts = key.split(":")
                if len(parts) >= 2:
                    nat = parts[1]
                    by_national[nat] = by_national.get(nat, 0) + 1
            if cursor == 0:
                break

        return {
            "unique_symbols": unique_symbols,
            "total_entries": total_entries,
            "by_national": by_national
        }

    # Backward compatibility methods (deprecated)
    async def load_symbols_by_national(self, national: str) -> int:
        """
        DEPRECATED: Use load_all_symbols() instead.
        특정 국가의 심볼만 Redis에 로드합니다.
        """
        logger.warning("[SymbolService] load_symbols_by_national is deprecated, use load_all_symbols instead")
        return await self.load_all_symbols()
