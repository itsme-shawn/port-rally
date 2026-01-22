import asyncio
import json
import time
import random
import os
from typing import List, Dict
import redis.asyncio as redis

# Redis 접속 정보 (환경변수 또는 localhost)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

SAMPLE_SIZE = 10000
QUERY_COUNT = 5000

def generate_dummy_data(count: int) -> List[Dict]:
    data = []
    for i in range(count):
        symbol = f"SYM{i:05d}"
        data.append({
            "symbol": symbol,
            "national": random.choice(["US", "KR", "JP", "HK"]),
            "market": random.choice(["NAS", "NYS", "KOSPI", "KOSDAQ"]),
            "name_ko": f"종목_{symbol}",
            "name_en": f"Stock_{symbol}",
            "currency": "USD",
            "type": "STOCK",
            "isin": f"US{i:010d}"
        })
    return data

# --- AS-IS: JSON List ---
async def bench_asis_write(r: redis.Redis, data: List[Dict]):
    start = time.perf_counter()
    pipe = r.pipeline()
    for item in data:
        key = f"bench:asis:{item['symbol']}"
        val = json.dumps([item], ensure_ascii=False)
        pipe.set(key, val)
    await pipe.execute()
    return time.perf_counter() - start

async def bench_asis_read(r: redis.Redis, symbols: List[str]):
    start = time.perf_counter()
    for symbol in symbols:
        val = await r.get(f"bench:asis:{symbol}")
        if val:
            _ = json.loads(val)
    return time.perf_counter() - start

# --- TO-BE: Set + Hash ---
async def bench_tobe_write(r: redis.Redis, data: List[Dict]):
    start = time.perf_counter()
    pipe = r.pipeline()
    for item in data:
        # Index
        idx_key = f"bench:tobe:idx:{item['symbol']}"
        market_key = f"{item['national']}:{item['market']}"
        pipe.sadd(idx_key, market_key)
        
        # Data
        data_key = f"bench:tobe:data:{market_key}:{item['symbol']}"
        pipe.hset(data_key, mapping=item)
    await pipe.execute()
    return time.perf_counter() - start

async def bench_tobe_read(r: redis.Redis, symbols: List[str]):
    start = time.perf_counter()
    for symbol in symbols:
        # 1. Get Markets
        markets = await r.smembers(f"bench:tobe:idx:{symbol}")
        # 2. Get Data (Sequential await - worst case)
        for m in markets:
            if isinstance(m, bytes): m = m.decode()
            await r.hgetall(f"bench:tobe:data:{m}:{symbol}")
    return time.perf_counter() - start

async def bench_tobe_read_optimized(r: redis.Redis, symbols: List[str]):
    """Pipeline을 사용하여 Network RTT를 줄인 버전"""
    start = time.perf_counter()
    
    # 1. 모든 인덱스 조회 (Pipeline)
    pipe = r.pipeline()
    for symbol in symbols:
        pipe.smembers(f"bench:tobe:idx:{symbol}")
    all_markets = await pipe.execute()
    
    # 2. 모든 데이터 조회 (Pipeline)
    pipe = r.pipeline()
    for i, markets in enumerate(all_markets):
        symbol = symbols[i]
        for m in markets:
            if isinstance(m, bytes): m = m.decode()
            pipe.hgetall(f"bench:tobe:data:{m}:{symbol}")
    await pipe.execute()
    
    return time.perf_counter() - start

async def main():
    print(f"Connecting to Redis: {REDIS_URL}")
    r = redis.from_url(REDIS_URL)
    
    try:
        await r.ping()
    except Exception as e:
        print(f"Redis Connection Failed: {e}")
        return

    print(f"Generating {SAMPLE_SIZE} items...")
    data = generate_dummy_data(SAMPLE_SIZE)
    symbols = [d['symbol'] for d in data[:QUERY_COUNT]]
    
    # --- AS-IS ---
    await r.flushdb()
    print("\n--- AS-IS (JSON String) ---")
    t_write = await bench_asis_write(r, data)
    print(f"Write: {t_write:.4f}s ({SAMPLE_SIZE/t_write:.0f} ops/s)")
    
    t_read = await bench_asis_read(r, symbols)
    print(f"Read : {t_read:.4f}s ({QUERY_COUNT/t_read:.0f} ops/s)")

    # --- TO-BE ---
    await r.flushdb()
    print("\n--- TO-BE (Set + Hash) ---")
    t_write = await bench_tobe_write(r, data)
    print(f"Write: {t_write:.4f}s ({SAMPLE_SIZE/t_write:.0f} ops/s)")
    
    t_read = await bench_tobe_read(r, symbols)
    print(f"Read (Naive)    : {t_read:.4f}s ({QUERY_COUNT/t_read:.0f} ops/s)")
    
    t_read_opt = await bench_tobe_read_optimized(r, symbols)
    print(f"Read (Pipeline) : {t_read_opt:.4f}s ({QUERY_COUNT/t_read_opt:.0f} ops/s)")
    
    await r.close()

if __name__ == "__main__":
    asyncio.run(main())
