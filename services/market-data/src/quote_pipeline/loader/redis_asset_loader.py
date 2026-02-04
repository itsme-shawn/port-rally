import asyncio
import json
import logging
import time
import argparse
import os
from typing import Dict, List, Any, Optional

from quote_pipeline.db import get_db
from quote_pipeline.redis_meta import meta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisAssetLoader:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.db = get_db()
        if redis_client:
            self.redis = redis_client
        else:
            # config.py의 전역 settings 객체가 없으므로 직접 환경변수 조회
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis = redis.from_url(redis_url, decode_responses=True)

    async def fetch_data(self):
        """DB에서 데이터 조회"""
        logger.info("[DB] Fetching assets from DB...")
        await self.db.connect()
        rows = await self.db.fetch("""
            SELECT 
                symbol, national, market, 
                name_ko, name_en, asset_type, currency, isin,
                asset_id
            FROM assets_master 
            ORDER BY symbol
        """)
        await self.db.close()
        logger.info(f"[DB] Fetched {len(rows)} rows.")
        return rows

    async def load_asis(self, rows, prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_METADATA", "symbol_metadata")):
        """
        DEPRECATED: AS-IS 구조는 2026-02-04에 제거되었습니다.
        Use load_tobe() instead.
        """
        logger.error(f"[AS-IS] DEPRECATED: symbol_metadata structure removed. Use --mode tobe instead.")
        raise NotImplementedError(
            "AS-IS (symbol_metadata) structure is deprecated and removed. "
            "Please use --mode tobe to load data in TO-BE (symbol_map + symbol_detail) structure."
        )

    async def load_tobe(self, rows, 
                        index_prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_MAP", "symbol_map"), 
                        data_prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_DETAIL", "symbol_detail")):
        """TO-BE: Set + Hash 구조 적재"""
        logger.info(f"[TO-BE] Loading started (Set + Hash) to index '{index_prefix}' and data '{data_prefix}'...")
        start_time = time.perf_counter()
        
        pipe = self.redis.pipeline()
        count = 0
        
        for row in rows:
            symbol = row['symbol']
            national = row['national']
            market = row['market']

            # Redis 키 생성 (from redis-meta.yml)
            map_key = meta.symbol_map(symbol=symbol)
            idx_key = map_key.build()

            detail_key = meta.symbol_detail(
                national=national,
                market=market,
                symbol=symbol
            )
            data_key = detail_key.build()

            market_key = f"{national}:{market}"

            metadata = {
                "asset_id": str(row['asset_id']),
                "symbol": symbol,
                "national": national,
                "market": market,
                "name_ko": row['name_ko'] or "",
                "name_en": row['name_en'] or "",
                "asset_type": row['asset_type'] or "",
                "currency": row['currency'] or "",
                "isin": row['isin'] or ""
            }
            
            pipe.sadd(idx_key, market_key)
            pipe.hset(data_key, mapping=metadata)
            
            count += 1
            if count % 1000 == 0:
                await pipe.execute()
                pipe = self.redis.pipeline()
                
        await pipe.execute()
        duration = time.perf_counter() - start_time
        logger.info(f"[TO-BE] Loaded {count} assets in {duration:.4f}s")
        return duration, count, index_prefix, data_prefix

async def main():
    parser = argparse.ArgumentParser(
        description="Load asset metadata into Redis (TO-BE structure only)"
    )
    parser.add_argument(
        "--mode",
        choices=["tobe"],
        default="tobe",
        help="DEPRECATED: Only 'tobe' mode is supported. AS-IS mode removed 2026-02-04."
    )
    # Prefix customization
    parser.add_argument("--prefix-tobe-index", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_MAP", "symbol_map"), help="Redis index key prefix for TO-BE mode")
    parser.add_argument("--prefix-tobe-data", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_DETAIL", "symbol_detail"), help="Redis data key prefix for TO-BE mode")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    loader = RedisAssetLoader()
    summary = []

    try:
        rows = await loader.fetch_data()

        # Only TO-BE mode supported
        dur, cnt, idx_pfx, data_pfx = await loader.load_tobe(
            rows,
            index_prefix=args.prefix_tobe_index,
            data_prefix=args.prefix_tobe_data
        )
        summary.append({"mode": "TO-BE(Idx)", "prefix": idx_pfx, "count": cnt, "duration": dur})
        summary.append({"mode": "TO-BE(Dat)", "prefix": data_pfx, "count": cnt, "duration": dur})

    finally:
        if hasattr(loader.redis, 'aclose'):
             await loader.redis.aclose()
        else:
             await loader.redis.close()

    print("\n" + "="*60)
    print(f"{'Mode':<10} | {'Key Prefix(es)':<35} | {'Count':<8} | {'Time(s)':<8}")
    print("-" * 60)
    for s in summary:
        print(f"{s['mode']:<10} | {s['prefix']:<35} | {s['count']:<8} | {s['duration']:<8.4f}")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
