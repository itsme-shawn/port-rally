#!/usr/bin/env python
"""Quote 조회 CLI.

Redis에 저장된 현재가 데이터를 조회합니다.

Usage:
    # 특정 심볼 조회
    python -m quote_pipeline.manage.quotes get NVDA

    # 전체 quote 키 목록
    python -m quote_pipeline.manage.quotes list
    python -m quote_pipeline.manage.quotes list --pattern "US:NAS:*"

    # 전체 현재가 조회 (테이블 형식)
    python -m quote_pipeline.manage.quotes all
    python -m quote_pipeline.manage.quotes all --pattern "US:NAS:*"

    # 실시간 구독 (Pub/Sub)
    python -m quote_pipeline.manage.quotes subscribe
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

from quote_pipeline.redis_meta import meta
from quote_pipeline.services.symbol_service import (
    SymbolService,
    SymbolNotFoundError,
    MultipleSymbolsFoundError,
)
from quote_pipeline.db import get_db

try:
    import redis.asyncio as aioredis
except ImportError:
    print("Error: redis package required. Install with: pip install redis")
    sys.exit(1)


DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEFAULT_CHANNEL = "quotes"


def format_price(value: Optional[str]) -> str:
    """가격 포맷팅."""
    if not value:
        return "-"
    try:
        num = float(value)
        if num >= 1000:
            return f"{num:,.2f}"
        elif num >= 1:
            return f"{num:.4f}"
        else:
            return f"{num:.8f}"
    except ValueError:
        return value


def format_timestamp(value: Optional[str]) -> str:
    """타임스탬프 포맷팅."""
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return value[:19] if len(value) > 19 else value


async def _get_quote_key_from_symbol(
    symbol_service: SymbolService, symbol: str
) -> Optional[str]:
    """심볼로부터 정확한 quote 키를 생성."""
    try:
        metadata = await symbol_service.get_metadata_by_symbol(symbol.upper())
        return meta.quote(
            national=metadata.national,
            exchange=metadata.exchange,
            symbol=metadata.symbol,
        ).build()
    except SymbolNotFoundError:
        return None
    except MultipleSymbolsFoundError:
        # 이 스크립트에서는 첫 번째 것을 사용하거나 혹은 에러 처리
        metadatas = await symbol_service.get_all_metadata_by_symbol(symbol.upper())
        if metadatas:
            m = metadatas[0]
            print(f"Warning: Multiple symbols found, using first one: {m.national}:{m.exchange}:{m.symbol}", file=sys.stderr)
            return meta.quote(
                national=m.national, exchange=m.exchange, symbol=m.symbol
            ).build()
        return None
    except Exception:
        return None


async def get_quote(
    client: aioredis.Redis, symbol_service: SymbolService, symbol: str
) -> None:
    """특정 심볼의 현재가 조회."""
    key = await _get_quote_key_from_symbol(symbol_service, symbol)

    if not key:
        print(f"Quote not found for: {symbol}")
        print(f"Reason: Symbol metadata not found in Redis cache.")
        return

    data = await client.hgetall(key)
    if data:
        print(f"\n{key}")
        print("-" * 50)

        # 주요 필드 우선 출력
        priority_fields = ["provider", "price", "volume", "timestamp", "updated_at", "change", "change_rate"]

        for field in priority_fields:
            if field in data:
                value = data[field]
                if field in ("price", "open", "high", "low", "change"):
                    value = format_price(value)
                elif field in ("timestamp", "updated_at"):
                    value = format_timestamp(value)
                elif field == "change_rate" and value:
                    try:
                        value = f"{float(value):.2f}%"
                    except ValueError:
                        pass
                print(f"  {field}: {value}")

        # 나머지 필드 출력
        other_fields = [f for f in data.keys() if f not in priority_fields]
        if other_fields:
            print()
            for field in sorted(other_fields):
                value = data[field]
                if field in ("open", "high", "low"):
                    value = format_price(value)
                print(f"  {field}: {value}")
    else:
        print(f"Quote data not found for key: {key}")


async def list_quotes(client: aioredis.Redis, pattern: Optional[str] = None) -> None:
    """quote 키 목록 조회."""
    prefix = meta.quote.get_prefix()
    search_pattern = f"{prefix}:{pattern}" if pattern else meta.quote.get_pattern()
    keys = await client.keys(search_pattern)

    if not keys:
        print(f"No quotes found matching: {search_pattern}")
        return

    print(f"\nFound {len(keys)} quote(s):\n")
    for key in sorted(keys):
        # prefix 제거하고 출력
        display_key = key.replace(f"{prefix}:", "", 1)
        print(f"  {display_key}")


async def all_quotes(client: aioredis.Redis, pattern: Optional[str] = None) -> None:
    """전체 현재가 테이블 형식으로 출력."""
    prefix = meta.quote.get_prefix()
    search_pattern = f"{prefix}:{pattern}" if pattern else meta.quote.get_pattern()
    keys = await client.keys(search_pattern)

    if not keys:
        print(f"No quotes found matching: {search_pattern}")
        return

    # 헤더
    print(f"\n{'Symbol':<30} {'Price':>15} {'Change':>10} {'Volume':>15} {'Updated':<20}")
    print("-" * 95)

    for key in sorted(keys):
        data = await client.hgetall(key)
        if not data:
            continue

        # Initialize variables defensively
        price = "-"
        change_str = "-"
        volume = "-"
        updated = "-"

        parsed = meta.quote.parse(key)
        symbol = parsed.get("symbol", key) if parsed else key

        price = format_price(data.get("price"))
        
        change_rate = data.get("change_rate", "")
        if change_rate:
            try:
                cr = float(change_rate)
                change_str = f"{cr:+.2f}%" if cr != 0 else "0.00%"
            except ValueError:
                change_str = "-"
        else:
            change_str = "-"

        volume = data.get("volume", "-")
        if volume and volume != "-":
            try:
                vol = float(volume)
                if vol >= 1_000_000:
                    volume = f"{vol/1_000_000:.2f}M"
                elif vol >= 1_000:
                    volume = f"{vol/1_000:.2f}K"
                else:
                    volume = f"{vol:.0f}"
            except ValueError:
                pass

        updated = format_timestamp(data.get("updated_at"))

        print(f"{symbol:<30} {price:>15} {change_str:>10} {volume:>15} {updated:<20}")

    print(f"\nTotal: {len(keys)} quote(s)")


async def subscribe_quotes(
    client: aioredis.Redis,
    channel: str = DEFAULT_CHANNEL,
) -> None:
    """실시간 시세 구독 (Pub/Sub)."""
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)

    print(f"Subscribed to channel: {channel}")
    print("Press Ctrl+C to stop\n")
    print(f"{'Time':<12} {'Provider':<8} {'Symbol':<20} {'Price':>15} {'Change':>10}")
    print("-" * 70)

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"])
                provider = data.get("provider", "?")
                symbol = data.get("symbol", "?")
                price = format_price(str(data.get("price", "")))

                change_rate = data.get("change_rate")
                if change_rate is not None:
                    try:
                        cr = float(change_rate)
                        change_str = f"{cr:+.2f}%"
                    except (ValueError, TypeError):
                        change_str = "-"
                else:
                    change_str = "-"

                now = datetime.now().strftime("%H:%M:%S")
                print(f"{now:<12} {provider:<8} {symbol:<20} {price:>15} {change_str:>10}")

            except json.JSONDecodeError:
                print(f"Invalid JSON: {message['data'][:50]}...")

    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quote 조회 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s get NVDA                  # NVDA 현재가 조회
  %(prog)s get KRW-BTC               # Upbit BTC 조회
  %(prog)s list                      # 전체 quote 키 목록
  %(prog)s list --pattern "US:NAS:*" # NAS 주식만
  %(prog)s all                       # 전체 현재가 테이블
  %(prog)s subscribe                 # 실시간 구독
        """,
    )
    parser.add_argument(
        "--redis-url",
        default=DEFAULT_REDIS_URL,
        help=f"Redis URL (default: {DEFAULT_REDIS_URL})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    get_parser = subparsers.add_parser("get", help="특정 심볼 현재가 조회")
    get_parser.add_argument("symbol", help="심볼 (예: NVDA, KRW-BTC)")

    # list
    list_parser = subparsers.add_parser("list", help="quote 키 목록")
    list_parser.add_argument("--pattern", "-p", help="검색 패턴 (예: US:NAS:*)")

    # all
    all_parser = subparsers.add_parser("all", help="전체 현재가 테이블")
    all_parser.add_argument("--pattern", "-p", help="검색 패턴")

    # subscribe
    sub_parser = subparsers.add_parser("subscribe", aliases=["sub"], help="실시간 구독")
    sub_parser.add_argument("--channel", "-c", default=DEFAULT_CHANNEL, help="Pub/Sub 채널")

    args = parser.parse_args()

    # Redis 및 DB, Service 초기화
    client = aioredis.from_url(args.redis_url, decode_responses=True)
    db_pool = get_db()
    symbol_service = SymbolService(db_pool=db_pool, redis_client=client)

    try:
        # 연결 테스트
        await client.ping()

        if args.command == "get":
            await get_quote(client, symbol_service, args.symbol)

        elif args.command == "list":
            await list_quotes(client, args.pattern)

        elif args.command == "all":
            await all_quotes(client, args.pattern)

        elif args.command in ("subscribe", "sub"):
            await subscribe_quotes(client, args.channel)

    except aioredis.ConnectionError as e:
        print(f"Error: Cannot connect to Redis at {args.redis_url}")
        print(f"Details: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        await client.aclose()
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
