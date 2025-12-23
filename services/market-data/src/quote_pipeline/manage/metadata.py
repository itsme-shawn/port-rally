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

logger = logging.getLogger(__name__)


async def get_metadata(symbol: str) -> None:
    """심볼의 메타데이터를 조회합니다.

    Args:
        symbol: 조회할 심볼
    """
    db = get_db()
    symbol_service = SymbolService(db_pool=db)

    # 캐시 로드
    print(f"Loading symbol metadata from DB...")
    loaded = await symbol_service.load_all_symbols()
    print(f"Loaded {loaded} symbols into cache\n")

    # 메타데이터 조회
    try:
        metadata = symbol_service.get_metadata_by_symbol(symbol)
        print(f"✅ Symbol: {metadata.symbol}")
        print(f"   National: {metadata.national}")
        print(f"   Exchange: {metadata.exchange}")
    except SymbolNotFoundError:
        print(f"❌ Symbol '{symbol}' not found in cache")
        sys.exit(1)
    except MultipleSymbolsFoundError as e:
        print(f"❌ Multiple entries found for '{symbol}' ({e.count} entries)")
        metadatas = symbol_service.get_all_metadata_by_symbol(symbol)
        for i, m in enumerate(metadatas, 1):
            print(f"   {i}. national={m.national}, exchange={m.exchange}")
        sys.exit(1)


async def list_metadata(national: Optional[str] = None) -> None:
    """메타데이터 목록을 조회합니다.

    Args:
        national: 국가 코드 필터 (Optional)
    """
    db = get_db()
    symbol_service = SymbolService(db_pool=db)

    # 캐시 로드
    print(f"Loading symbol metadata from DB...")
    loaded = await symbol_service.load_all_symbols()
    print(f"Loaded {loaded} symbols into cache\n")

    # 목록 조회
    if national:
        symbols = symbol_service.get_symbols_by_national(national)
        print(f"Symbols (national={national}): {len(symbols)} symbols")
    else:
        symbols = symbol_service.get_all_symbols()
        print(f"All symbols: {len(symbols)} symbols")

    # 샘플 출력 (최대 20개)
    for symbol in symbols[:20]:
        metadatas = symbol_service.get_all_metadata_by_symbol(symbol)
        for metadata in metadatas:
            print(f"  {metadata.symbol:12s} | {metadata.national:4s} | {metadata.exchange}")

    if len(symbols) > 20:
        print(f"  ... and {len(symbols) - 20} more symbols")


async def show_stats() -> None:
    """캐시 통계를 출력합니다."""
    db = get_db()
    symbol_service = SymbolService(db_pool=db)

    # 캐시 로드
    print(f"Loading symbol metadata from DB...")
    loaded = await symbol_service.load_all_symbols()
    print(f"Loaded {loaded} symbols into cache\n")

    # 통계 출력
    cache_size = symbol_service.get_cache_size()
    total_count = symbol_service.get_total_count()

    print(f"Cache Statistics:")
    print(f"  Unique symbols: {cache_size}")
    print(f"  Total entries: {total_count}")

    # 국가별 통계
    nationals = set()
    symbols = symbol_service.get_all_symbols()
    for symbol in symbols:
        metadatas = symbol_service.get_all_metadata_by_symbol(symbol)
        for metadata in metadatas:
            nationals.add(metadata.national)

    print(f"\nBy National:")
    for national in sorted(nationals):
        count = len(symbol_service.get_symbols_by_national(national))
        print(f"  {national}: {count} symbols")


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
