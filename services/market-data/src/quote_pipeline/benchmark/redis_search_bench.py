import asyncio
import json
import time
import logging
import argparse
import sys
import os
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis 접속 정보 직접 조회
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def benchmark_asis_no_pipe(redis_client, symbols, prefix="symbol_metadata_DEPRECATED"):
    """AS-IS 구조-1 : Pipe 미사용 (순차 조회)"""
    start = time.perf_counter()
    count = 0
    for symbol in symbols:
        key = f"{prefix}:{symbol}"
        data = await redis_client.get(key)
        if data:
            try:
                _ = json.loads(data)
                count += 1
            except:
                pass
    duration = time.perf_counter() - start
    return duration, count

async def benchmark_asis_pipe(redis_client, symbols, prefix="symbol_metadata_DEPRECATED"):
    """AS-IS 구조-2 : Pipe 사용 (일괄 조회)"""
    start = time.perf_counter()
    count = 0
    pipe = redis_client.pipeline()
    
    for symbol in symbols:
        key = f"{prefix}:{symbol}"
        pipe.get(key)
        
    results = await pipe.execute()
    
    for data in results:
        if data:
            try:
                _ = json.loads(data)
                count += 1
            except:
                pass
    duration = time.perf_counter() - start
    return duration, count

async def benchmark_tobe_no_pipe(redis_client, symbols, 
                                 index_prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_MAP", "symbol_map"), 
                                 data_prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_DETAIL", "symbol_detail")):
    """TO-BE 구조-1 : Pipe 미사용 (완전 순차 조회)"""
    start = time.perf_counter()
    count = 0
    for symbol in symbols:
        # 1. 인덱스 조회
        idx_key = f"{index_prefix}:{symbol}"
        markets = await redis_client.smembers(idx_key)
        
        # 2. 데이터 조회
        if markets:
            for m in markets:
                market_key = m.decode() if isinstance(m, bytes) else m
                data_key = f"{data_prefix}:{market_key}:{symbol}"
                await redis_client.hgetall(data_key)
            count += 1
    duration = time.perf_counter() - start
    return duration, count

async def benchmark_tobe_pipe(redis_client, symbols, 
                              index_prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_MAP", "symbol_map"), 
                              data_prefix=os.getenv("REDIS_KEY_PREFIX_SYMBOL_DETAIL", "symbol_detail")):
    """TO-BE 구조-2 : Pipe 사용 (단계별 일괄 조회)"""
    start = time.perf_counter()
    count = 0
    
    # Step 1: 모든 심볼의 인덱스(시장 목록) 조회
    pipe_idx = redis_client.pipeline()
    for symbol in symbols:
        pipe_idx.smembers(f"{index_prefix}:{symbol}")
    
    markets_list = await pipe_idx.execute()
    
    # Step 2: 조회된 시장 정보를 바탕으로 데이터 조회 구성
    pipe_data = redis_client.pipeline()
    valid_indices = []
    
    for i, markets in enumerate(markets_list):
        if markets:
            valid_indices.append(i)
            symbol = symbols[i]
            for m in markets:
                market_key = m.decode() if isinstance(m, bytes) else m
                data_key = f"{data_prefix}:{market_key}:{symbol}"
                pipe_data.hgetall(data_key)
    
    # 데이터 조회 실행 (결과는 개별 데이터지만, 여기선 횟수 카운트가 목적)
    if valid_indices:
        await pipe_data.execute()
        count = len(valid_indices) # 데이터를 찾은 심볼 수
        
    duration = time.perf_counter() - start
    return duration, count

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000, help="Number of queries")
    parser.add_argument("--prefix-asis", default="symbol_metadata_DEPRECATED", help="DEPRECATED: AS-IS mode removed")
    parser.add_argument("--prefix-tobe-index", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_MAP", "symbol_map"), help="Redis index key prefix for TO-BE mode")
    parser.add_argument("--prefix-tobe-data", default=os.getenv("REDIS_KEY_PREFIX_SYMBOL_DETAIL", "symbol_detail"), help="Redis data key prefix for TO-BE mode")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    r = redis.from_url(REDIS_URL, decode_responses=False)
    
    # 테스트용 심볼 샘플링
    logger.info(f"🔍 Scanning for test symbols using prefix '{args.prefix_asis}'...")
    keys = []
    cursor = 0
    scan_match = f"{args.prefix_asis}:*"
    
    try:
        while len(keys) < args.count:
            cursor, res = await r.scan(cursor, match=scan_match, count=1000)
            for k in res:
                key_str = k.decode()
                symbol = key_str.split(":", 1)[1]
                keys.append(symbol)
            if cursor == 0: break
    except Exception as e:
        logger.error(f"Error scanning keys: {e}")
        sys.exit(1)
    
    if not keys:
        logger.error(f"❌ No data found with match '{scan_match}'. Please run loader first.")
        sys.exit(1)

    symbols = keys[:args.count]
    logger.info(f"🚀 Benchmarking Search Performance ({len(symbols)} items)")
    print("-" * 60)
    print(f"{'Metric':<30} | {'Time (s)':<10} | {'Avg (ms)':<10} | {'Count':<5}")
    print("-" * 60)

    # Helper to print row
    def print_result(name, t, c):
        avg = (t / c * 1000) if c > 0 else 0
        print(f"{name:<30} | {t:<10.4f} | {avg:<10.3f} | {c:<5}")

    # 1. AS-IS No Pipe
    t1, c1 = await benchmark_asis_no_pipe(r, symbols, args.prefix_asis)
    print_result("AS-IS (No Pipe)", t1, c1)

    # 2. AS-IS Pipe
    t2, c2 = await benchmark_asis_pipe(r, symbols, args.prefix_asis)
    print_result("AS-IS (Pipe)", t2, c2)

    # 3. TO-BE No Pipe
    t3, c3 = await benchmark_tobe_no_pipe(r, symbols, args.prefix_tobe_index, args.prefix_tobe_data)
    print_result("TO-BE (No Pipe)", t3, c3)

    # 4. TO-BE Pipe
    t4, c4 = await benchmark_tobe_pipe(r, symbols, args.prefix_tobe_index, args.prefix_tobe_data)
    print_result("TO-BE (Pipe)", t4, c4)

    print("-" * 60)
    
    if hasattr(r, 'aclose'):
        await r.aclose()
    else:
        await r.close()

if __name__ == "__main__":
    asyncio.run(main())
