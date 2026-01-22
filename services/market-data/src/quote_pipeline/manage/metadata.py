#!/usr/bin/env python
"""심볼 메타데이터 조회 CLI.

Usage:
    python -m quote_pipeline.manage metadata get <symbol>
    python -m quote_pipeline.manage metadata list [--national=<code>]
    python -m quote_pipeline.manage metadata stats

Examples:
    python -m quote_pipeline.manage metadata get NVDA
    python -m quote_pipeline.manage metadata list --national=US
    python -m quote_pipeline.manage metadata stats
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional

from quote_pipeline.db import get_db
from quote_pipeline.services.symbol_service import (
    SymbolService,
    SymbolNotFoundError,
    MultipleSymbolsFoundError,
)
from quote_pipeline.loader.redis_asset_loader import RedisAssetLoader

logger = logging.getLogger(__name__)


async def get_metadata(symbol: str) -> None:
    """심볼의 메타데이터를 조회합니다.

    Args:
        symbol: 조회할 심볼
    """
    try:
        import redis.asyncio as aioredis
    except ImportError:
        print("Error: redis package required. Install with: pip install redis")
        sys.exit(1)

    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.from_url(redis_url, decode_responses=True)

    try:
        await redis_client.ping()
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        sys.exit(1)

    db = get_db()
    symbol_service = SymbolService(db_pool=db, redis_client=redis_client)

    # Redis 캐시 확인
    cache_size = await symbol_service.get_cache_size()
    if cache_size == 0:
        print(f"⏳ Loading symbol metadata from DB to Redis using RedisAssetLoader...")
        loader = RedisAssetLoader(redis_client=redis_client)
        rows = await loader.fetch_data()
        dur, count, _ = await loader.load_asis(rows)
        print(f"✅ Loaded {count} symbols into Redis in {dur:.4f}s\n")
    else:
        print(f"✅ Redis cache already loaded ({cache_size} unique symbols)\n")

    # 메타데이터 조회
    try:
        metadata = await symbol_service.get_metadata_by_symbol(symbol)
        print(f"✅ Symbol: {metadata.symbol}")
        print(f"   National: {metadata.national}")
        print(f"   Exchange: {metadata.exchange}")
    except SymbolNotFoundError:
        print(f"❌ Symbol '{symbol}' not found in Redis")
        sys.exit(1)
    except MultipleSymbolsFoundError as e:
        print(f"❌ Multiple entries found for '{symbol}' ({e.count} entries)")
        metadatas = await symbol_service.get_all_metadata_by_symbol(symbol)
        for i, m in enumerate(metadatas, 1):
            print(f"   {i}. national={m.national}, exchange={m.exchange}")
        sys.exit(1)
    finally:
        await redis_client.aclose()


async def list_metadata(national: Optional[str] = None) -> None:
    """메타데이터 목록을 조회합니다.

    Args:
        national: 국가 코드 필터 (Optional)
    """
    try:
        import redis.asyncio as aioredis
    except ImportError:
        print("Error: redis package required. Install with: pip install redis")
        sys.exit(1)

    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.from_url(redis_url, decode_responses=True)

    try:
        await redis_client.ping()
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        sys.exit(1)

    db = get_db()
    symbol_service = SymbolService(db_pool=db, redis_client=redis_client)

    try:
        # Redis 캐시 확인
        cache_size = await symbol_service.get_cache_size()
        if cache_size == 0:
            print(f"⏳ Loading symbol metadata from DB to Redis using RedisAssetLoader...")
            loader = RedisAssetLoader(redis_client=redis_client)
            rows = await loader.fetch_data()
            dur, count, _ = await loader.load_asis(rows)
            print(f"✅ Loaded {count} symbols into Redis in {dur:.4f}s\n")
        else:
            print(f"✅ Redis cache already loaded ({cache_size} unique symbols)\n")

        # 목록 조회
        if national:
            symbols = await symbol_service.get_symbols_by_national(national)
            print(f"Symbols (national={national}): {len(symbols)} symbols")
        else:
            symbols = await symbol_service.get_all_symbols()
            print(f"All symbols: {len(symbols)} symbols")

        # 샘플 출력 (최대 20개)
        for symbol in symbols[:20]:
            metadatas = await symbol_service.get_all_metadata_by_symbol(symbol)
            for metadata in metadatas:
                print(f"  {metadata.symbol:12s} | {metadata.national:4s} | {metadata.exchange}")

        if len(symbols) > 20:
            print(f"  ... and {len(symbols) - 20} more symbols")
    finally:
        await redis_client.aclose()


async def show_stats() -> None:
    """캐시 통계를 출력합니다."""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        print("Error: redis package required. Install with: pip install redis")
        sys.exit(1)

    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = aioredis.from_url(redis_url, decode_responses=True)

    try:
        await redis_client.ping()
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        sys.exit(1)

    db = get_db()
    symbol_service = SymbolService(db_pool=db, redis_client=redis_client)

    try:
        # Redis 캐시 확인
        cache_size = await symbol_service.get_cache_size()
        if cache_size == 0:
            print(f"⏳ Loading symbol metadata from DB to Redis using RedisAssetLoader...")
            loader = RedisAssetLoader(redis_client=redis_client)
            rows = await loader.fetch_data()
            dur, count, _ = await loader.load_asis(rows)
            print(f"✅ Loaded {count} symbols into Redis in {dur:.4f}s\n")
        else:
            print(f"✅ Redis cache already loaded ({cache_size} unique symbols)\n")

        # 통계 출력
        cache_size = await symbol_service.get_cache_size()
        total_count = await symbol_service.get_total_count()

        print(f"Redis Cache Statistics:")
        print(f"  Unique symbols: {cache_size}")
        print(f"  Total entries: {total_count}")

        # 국가별 통계
        nationals = set()
        symbols = await symbol_service.get_all_symbols()
        for symbol in symbols:
            metadatas = await symbol_service.get_all_metadata_by_symbol(symbol)
            for metadata in metadatas:
                nationals.add(metadata.national)

        print(f"\nBy National:")
        for national in sorted(nationals):
            count = len(await symbol_service.get_symbols_by_national(national))
            print(f"  {national}: {count} symbols")
    finally:
        await redis_client.aclose()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="심볼 메타데이터 조회",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m quote_pipeline.manage metadata get NVDA
  python -m quote_pipeline.manage metadata list --national=US
  python -m quote_pipeline.manage metadata stats
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # get 서브커맨드
    parser_get = subparsers.add_parser("get", help="Get metadata for a symbol")
    parser_get.add_argument("symbol", help="Symbol to query")

    # list 서브커맨드
    parser_list = subparsers.add_parser("list", help="List all metadata")
    parser_list.add_argument("--national", help="Filter by national code (e.g., US, KR)")

    # stats 서브커맨드
    subparsers.add_parser("stats", help="Show cache statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "get":
        await get_metadata(args.symbol)
    elif args.command == "list":
        await list_metadata(args.national)
    elif args.command == "stats":
        await show_stats()


if __name__ == "__main__":
    asyncio.run(main())
