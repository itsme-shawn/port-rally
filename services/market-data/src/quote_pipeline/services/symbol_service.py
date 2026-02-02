"""Symbol service - 심볼 메타데이터 관리 서비스."""

import json
import logging
import os
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

    def to_json(self) -> str:
        """JSON 문자열로 변환."""
        return json.dumps(asdict(self), ensure_ascii=False)

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

    @classmethod
    def from_json(cls, data: str) -> "SymbolMetadata":
        """JSON 문자열에서 생성."""
        return cls.from_dict(json.loads(data))


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
    심볼 메타데이터 관리 서비스 (Redis 기반).

    DB에서 (symbol, national, exchange) 정보를 Redis에 저장하고,
    모든 프로세스가 Redis를 통해 메타데이터를 조회합니다.

    Redis 키 구조:
        symbol_metadata:{symbol} → JSON array of SymbolMetadata
        예: symbol_metadata:TSLA → [{"symbol": "TSLA", "national": "US", "exchange": "NAS"}]
    """

    REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX_SYMBOL_METADATA", "symbol_metadata")

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
        DB에서 모든 심볼 메타데이터를 Redis에 로드합니다.

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

            # 기존 Redis 캐시 삭제 (symbol_metadata:* 키들)
            pattern = f"{self.REDIS_KEY_PREFIX}:*"
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
                if cursor == 0:
                    break

            if deleted_count > 0:
                logger.info("[SymbolService] Cleared %d existing Redis keys", deleted_count)

            # 심볼별로 그룹화
            symbol_map: Dict[str, List[SymbolMetadata]] = {}
            for row in rows:
                metadata = SymbolMetadata.from_dict(dict(row))
                if metadata.symbol not in symbol_map:
                    symbol_map[metadata.symbol] = []
                symbol_map[metadata.symbol].append(metadata)

            # Redis에 일괄 저장 (pipeline 사용)
            pipe = self.redis_client.pipeline()
            for symbol, metadatas in symbol_map.items():
                # Redis 키 생성 (from redis-meta.yml)
                metadata_key = meta.symbol_metadata(symbol=symbol)
                key = metadata_key.build()

                # List[SymbolMetadata]를 JSON array로 변환
                json_array = json.dumps([asdict(m) for m in metadatas], ensure_ascii=False)
                pipe.set(key, json_array)

            await pipe.execute()

            total_count = len(rows)
            unique_count = len(symbol_map)
            logger.info(
                "[SymbolService] Loaded %d symbols (%d unique) into Redis",
                total_count,
                unique_count,
            )
            return total_count

        except Exception:
            logger.error("[SymbolService] Failed to load symbols from DB to Redis", exc_info=True)
            return 0

    async def load_symbols_by_national(self, national: str) -> int:
        """
        특정 국가의 심볼만 Redis에 로드합니다.

        Args:
            national: 국가 코드 (KR, US, HK 등)

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
                WHERE national = $1 
                ORDER BY symbol
                """,
                national,
            )

            # Redis에서 해당 national의 기존 데이터 제거 후 업데이트
            # 모든 symbol_metadata 키를 스캔하여 해당 national 포함 여부 확인
            pattern = f"{self.REDIS_KEY_PREFIX}:*"
            cursor = 0
            pipe = self.redis_client.pipeline()

            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                for key in keys:
                    data = await self.redis_client.get(key)
                    if data:
                        metadatas_list = json.loads(data)
                        # 해당 national 제거
                        filtered = [m for m in metadatas_list if m.get("national") != national]
                        if not filtered:
                            pipe.delete(key)
                        elif len(filtered) != len(metadatas_list):
                            pipe.set(key, json.dumps(filtered, ensure_ascii=False))
                if cursor == 0:
                    break

            # 새로운 데이터 추가
            symbol_map: Dict[str, List[SymbolMetadata]] = {}
            for row in rows:
                metadata = SymbolMetadata.from_dict(dict(row))
                if metadata.symbol not in symbol_map:
                    symbol_map[metadata.symbol] = []
                symbol_map[metadata.symbol].append(metadata)

            for symbol, metadatas in symbol_map.items():
                # Redis 키 생성 (from redis-meta.yml)
                metadata_key = meta.symbol_metadata(symbol=symbol)
                key = metadata_key.build()

                # 기존 데이터가 있으면 병합
                existing_data = await self.redis_client.get(key)
                if existing_data:
                    existing = json.loads(existing_data)
                    all_metadatas = [SymbolMetadata.from_dict(m) for m in existing] + metadatas
                    json_array = json.dumps([asdict(m) for m in all_metadatas], ensure_ascii=False)
                else:
                    json_array = json.dumps([asdict(m) for m in metadatas], ensure_ascii=False)
                pipe.set(key, json_array)

            await pipe.execute()

            count = len(rows)
            logger.info("[SymbolService] Loaded %d symbols (national=%s) into Redis", count, national)
            return count

        except Exception:
            logger.error(
                "[SymbolService] Failed to load symbols (national=%s) from DB to Redis",
                national,
                exc_info=True,
            )
            return 0

    async def get_metadata_by_symbol(self, symbol: str) -> SymbolMetadata:
        """
        심볼의 메타데이터를 Redis에서 조회합니다.

        Args:
            symbol: 종목 심볼

        Returns:
            SymbolMetadata 객체

        Raises:
            SymbolNotFoundError: 심볼을 찾을 수 없을 때
            MultipleSymbolsFoundError: 동일 심볼이 여러 개 있을 때
        """
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        key = f"{self.REDIS_KEY_PREFIX}:{symbol}"
        data = await self.redis_client.get(key)

        if not data:
            raise SymbolNotFoundError(symbol)

        metadatas_list = json.loads(data)
        metadatas = [SymbolMetadata.from_dict(m) for m in metadatas_list]

        if len(metadatas) == 0:
            raise SymbolNotFoundError(symbol)

        if len(metadatas) > 1:
            raise MultipleSymbolsFoundError(symbol, len(metadatas))

        return metadatas[0]

    async def get_all_metadata_by_symbol(self, symbol: str) -> List[SymbolMetadata]:
        """
        심볼의 모든 메타데이터를 Redis에서 조회합니다 (동일 심볼이 여러 국가에 있을 수 있음).

        Args:
            symbol: 종목 심볼

        Returns:
            SymbolMetadata 리스트

        Raises:
            SymbolNotFoundError: 심볼을 찾을 수 없을 때
        """
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        key = f"{self.REDIS_KEY_PREFIX}:{symbol}"
        data = await self.redis_client.get(key)

        if not data:
            raise SymbolNotFoundError(symbol)

        metadatas_list = json.loads(data)
        return [SymbolMetadata.from_dict(m) for m in metadatas_list]

    async def set_metadata(self, metadata: SymbolMetadata) -> None:
        """
        심볼 메타데이터를 Redis에 저장합니다.

        Args:
            metadata: SymbolMetadata 객체
        """
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        key = f"{self.REDIS_KEY_PREFIX}:{metadata.symbol}"

        # 기존 데이터 조회
        existing_data = await self.redis_client.get(key)
        if existing_data:
            metadatas_list = json.loads(existing_data)
            metadatas = [SymbolMetadata.from_dict(m) for m in metadatas_list]

            # 동일한 (symbol, national) 조합이 있으면 제거
            metadatas = [
                m
                for m in metadatas
                if not (m.symbol == metadata.symbol and m.national == metadata.national)
            ]
            metadatas.append(metadata)
        else:
            metadatas = [metadata]

        # Redis에 저장
        json_array = json.dumps([asdict(m) for m in metadatas], ensure_ascii=False)
        await self.redis_client.set(key, json_array)

    async def clear_cache(self) -> None:
        """Redis 캐시를 초기화합니다."""
        if not self.redis_client:
            raise RuntimeError("[SymbolService] Redis client not available")

        pattern = f"{self.REDIS_KEY_PREFIX}:*"
        cursor = 0
        deleted_count = 0

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

        pattern = f"{self.REDIS_KEY_PREFIX}:*"
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

        pattern = f"{self.REDIS_KEY_PREFIX}:*"
        cursor = 0
        total = 0

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    metadatas_list = json.loads(data)
                    total += len(metadatas_list)
            if cursor == 0:
                break

        return total

    async def get_all_symbols(self) -> List[str]:
        """Redis에 저장된 모든 심볼을 반환합니다."""
        if not self.redis_client:
            return []

        pattern = f"{self.REDIS_KEY_PREFIX}:*"
        cursor = 0
        symbols = []

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                # key 형식: symbol_metadata:SYMBOL
                symbol = key.split(":", 1)[1] if ":" in key else key
                symbols.append(symbol)
            if cursor == 0:
                break

        return sorted(symbols)

    async def get_symbols_by_national(self, national: str) -> List[str]:
        """특정 국가의 심볼만 반환합니다."""
        if not self.redis_client:
            return []

        pattern = f"{self.REDIS_KEY_PREFIX}:*"
        cursor = 0
        symbols = set()

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    metadatas_list = json.loads(data)
                    if any(m.get("national") == national for m in metadatas_list):
                        symbol = key.split(":", 1)[1] if ":" in key else key
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

        pattern = f"{self.REDIS_KEY_PREFIX}:*"
        cursor = 0
        unique_symbols = 0
        total_entries = 0
        by_national = {}

        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=1000)
            unique_symbols += len(keys)

            if keys:
                # Pipeline을 사용하여 한 번에 조회
                pipe = self.redis_client.pipeline()
                for key in keys:
                    pipe.get(key)
                results = await pipe.execute()

                for data in results:
                    if data:
                        metadatas_list = json.loads(data)
                        total_entries += len(metadatas_list)
                        for m in metadatas_list:
                            nat = m.get("national", "Unknown")
                            by_national[nat] = by_national.get(nat, 0) + 1

            if cursor == 0:
                break

        return {
            "unique_symbols": unique_symbols,
            "total_entries": total_entries,
            "by_national": by_national
        }