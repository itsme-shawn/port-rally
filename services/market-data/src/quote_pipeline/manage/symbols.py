#!/usr/bin/env python
"""Active Symbols 관리 CLI.

클라이언트별 active_symbols CRUD 기능을 제공합니다.

Usage:
    # 조회
    python -m quote_pipeline.manage.symbols list kis
    python -m quote_pipeline.manage.symbols list upbit
    python -m quote_pipeline.manage.symbols list --all

    # 추가
    python -m quote_pipeline.manage.symbols add kis NVDA AAPL TSLA
    python -m quote_pipeline.manage.symbols add upbit KRW-BTC KRW-ETH

    # 삭제
    python -m quote_pipeline.manage.symbols remove kis NVDA
    python -m quote_pipeline.manage.symbols remove upbit KRW-BTC

    # 전체 삭제
    python -m quote_pipeline.manage.symbols clear kis
    python -m quote_pipeline.manage.symbols clear --all

    # Redis URL 지정 (기본: redis://localhost:6379)
    python -m quote_pipeline.manage.symbols --redis-url redis://localhost:6379 list kis
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    print("Error: redis package required. Install with: pip install redis")
    sys.exit(1)


PROVIDERS = ["kis", "upbit", "binance"]
DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEFAULT_PREFIX = "active_symbols"


async def list_symbols(
    client: aioredis.Redis,
    provider: Optional[str] = None,
    prefix: str = DEFAULT_PREFIX,
) -> None:
    """클라이언트별 active_symbols 조회."""
    providers_to_check = [provider] if provider else PROVIDERS

    for p in providers_to_check:
        key = f"{prefix}:{p}"
        symbols = await client.smembers(key)
        count = len(symbols) if symbols else 0

        print(f"\n[{p}] ({count} symbols)")
        if symbols:
            for sym in sorted(symbols):
                print(f"  - {sym}")
        else:
            print("  (empty)")


async def add_symbols(
    client: aioredis.Redis,
    provider: str,
    symbols: list[str],
    prefix: str = DEFAULT_PREFIX,
) -> None:
    """active_symbols에 심볼 추가."""
    if not symbols:
        print("Error: No symbols specified")
        return

    key = f"{prefix}:{provider}"
    added = await client.sadd(key, *symbols)
    print(f"[{provider}] Added {added} symbol(s): {', '.join(symbols)}")

    # 현재 상태 출력
    current = await client.smembers(key)
    print(f"[{provider}] Current count: {len(current)}")


async def remove_symbols(
    client: aioredis.Redis,
    provider: str,
    symbols: list[str],
    prefix: str = DEFAULT_PREFIX,
) -> None:
    """active_symbols에서 심볼 삭제."""
    if not symbols:
        print("Error: No symbols specified")
        return

    key = f"{prefix}:{provider}"
    removed = await client.srem(key, *symbols)
    print(f"[{provider}] Removed {removed} symbol(s): {', '.join(symbols)}")

    # 현재 상태 출력
    current = await client.smembers(key)
    print(f"[{provider}] Current count: {len(current)}")


async def clear_symbols(
    client: aioredis.Redis,
    provider: Optional[str] = None,
    prefix: str = DEFAULT_PREFIX,
) -> None:
    """active_symbols 전체 삭제."""
    providers_to_clear = [provider] if provider else PROVIDERS

    for p in providers_to_clear:
        key = f"{prefix}:{p}"
        deleted = await client.delete(key)
        if deleted:
            print(f"[{p}] Cleared active_symbols")
        else:
            print(f"[{p}] Already empty")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Active Symbols 관리 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list kis              # KIS active_symbols 조회
  %(prog)s list --all            # 전체 조회
  %(prog)s add kis NVDA AAPL     # KIS에 심볼 추가
  %(prog)s remove kis NVDA       # KIS에서 심볼 삭제
  %(prog)s clear kis             # KIS active_symbols 전체 삭제
  %(prog)s clear --all           # 전체 삭제
        """,
    )
    parser.add_argument(
        "--redis-url",
        default=DEFAULT_REDIS_URL,
        help=f"Redis URL (default: {DEFAULT_REDIS_URL})",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"Redis key prefix (default: {DEFAULT_PREFIX})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    list_parser = subparsers.add_parser("list", help="active_symbols 조회")
    list_parser.add_argument("provider", nargs="?", choices=PROVIDERS, help="Provider (kis/upbit/binance)")
    list_parser.add_argument("--all", "-a", action="store_true", help="전체 provider 조회")

    # add
    add_parser = subparsers.add_parser("add", help="심볼 추가")
    add_parser.add_argument("provider", choices=PROVIDERS, help="Provider")
    add_parser.add_argument("symbols", nargs="+", help="추가할 심볼들")

    # remove
    remove_parser = subparsers.add_parser("remove", help="심볼 삭제")
    remove_parser.add_argument("provider", choices=PROVIDERS, help="Provider")
    remove_parser.add_argument("symbols", nargs="+", help="삭제할 심볼들")

    # clear
    clear_parser = subparsers.add_parser("clear", help="전체 삭제")
    clear_parser.add_argument("provider", nargs="?", choices=PROVIDERS, help="Provider")
    clear_parser.add_argument("--all", "-a", action="store_true", help="전체 provider 삭제")

    args = parser.parse_args()

    # Redis 연결
    client = aioredis.from_url(args.redis_url, decode_responses=True)

    try:
        # 연결 테스트
        await client.ping()
        print(f"Connected to Redis: {args.redis_url}\n")

        if args.command == "list":
            if args.all or not args.provider:
                await list_symbols(client, prefix=args.prefix)
            else:
                await list_symbols(client, args.provider, prefix=args.prefix)

        elif args.command == "add":
            await add_symbols(client, args.provider, args.symbols, prefix=args.prefix)

        elif args.command == "remove":
            await remove_symbols(client, args.provider, args.symbols, prefix=args.prefix)

        elif args.command == "clear":
            if args.all:
                await clear_symbols(client, prefix=args.prefix)
            elif args.provider:
                await clear_symbols(client, args.provider, prefix=args.prefix)
            else:
                parser.error("clear requires --all or provider name")

    except aioredis.ConnectionError as e:
        print(f"Error: Cannot connect to Redis at {args.redis_url}")
        print(f"Details: {e}")
        sys.exit(1)
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
