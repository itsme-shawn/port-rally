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
        """AS-IS: JSON List 구조 적재"""
        logger.info(f"[AS-IS] Loading started (JSON List) to key prefix '{prefix}'...")
        start_time = time.perf_counter()
        
        pipe = self.redis.pipeline()
        count = 0
        
        # 심볼별 그룹화
        grouped = {}
        for row in rows:
            symbol = row['symbol']
            if symbol not in grouped: grouped[symbol] = []
            grouped[symbol].append({
                "symbol": symbol,
                "national": row['national'],
                "market": row['market'],
                "name_ko": row['name_ko'] or "",
                "name_en": row['name_en'] or "",
                "asset_type": row['asset_type'] or "",
                "currency": row['currency'] or "",
                "isin": row['isin'] or "",
                "asset_id": str(row['asset_id'])
            })
            
        for symbol, items in grouped.items():
            # Redis 키 생성 (from redis-meta.yml)
            metadata_key = meta.symbol_metadata(symbol=symbol)
            key = metadata_key.build()

            pipe.set(key, json.dumps(items, ensure_ascii=False))
            count += 1
            if count % 1000 == 0:
                await pipe.execute()
                pipe = self.redis.pipeline()
        
        await pipe.execute()
        duration = time.perf_counter() - start_time
        logger.info(f"[AS-IS] Loaded {count} keys in {duration:.4f}s")
        return duration, count, prefix

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["asis", "tobe", "both"], default="both")
    # Prefix customization with experimental defaults
    parser.add_argument("--prefix-asis", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_METADATA", "symbol_metadata"), help="Redis key prefix for AS-IS mode")
    parser.add_argument("--prefix-tobe-index", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_MAP", "symbol_map"), help="Redis index key prefix for TO-BE mode")
    parser.add_argument("--prefix-tobe-data", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_DETAIL", "symbol_detail"), help="Redis data key prefix for TO-BE mode")
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    
    loader = RedisAssetLoader()
    summary = []
    
    try:
        rows = await loader.fetch_data()
        
        if args.mode in ["asis", "both"]:
            dur, cnt, pfx = await loader.load_asis(rows, prefix=args.prefix_asis)
            summary.append({"mode": "AS-IS", "prefix": pfx, "count": cnt, "duration": dur})
        
        if args.mode in ["tobe", "both"]:
            dur, cnt, idx_pfx, data_pfx = await loader.load_tobe(rows, index_prefix=args.prefix_tobe_index, data_prefix=args.prefix_tobe_data)
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
