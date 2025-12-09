import argparse
import asyncio
import logging
from typing import List
import os

from quote_pipeline.config import Provider, Settings
from quote_pipeline.logging_config import configure_logging
from quote_pipeline.pipeline import build_ingestor, build_sink
from quote_pipeline.active_symbols import manage_dynamic_ingestor


def parse_symbols(symbols_str: str) -> List[str]:
    return [s.strip() for s in symbols_str.split(",") if s.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PortRally market data Phase 0 PoC")
    parser.add_argument(
        "--provider",
        choices=[p.value for p in Provider],
        default=Provider.upbit.value,
        help="거래소/데이터 소스",
    )
    parser.add_argument(
        "--symbols",
        default="",
        help="콤마로 구분된 심볼 리스트 (예: KRW-BTC,KRW-ETH / btcusdt,ethusdt / NVDA). 미지정 시 빈 리스트.",
    )
    parser.add_argument(
        "--channel",
        default=None,
        help="채널 override (upbit: ticker/trade/orderbook, binance: trade/bookTicker 등)",
    )
    parser.add_argument(
        "--redis-url",
        default=None,
        help="Redis sink URL. 미지정 시 stdout sink 사용",
    )
    parser.add_argument(
        "--redis-channel",
        default=None,
        help="Redis Pub/Sub 채널명 (기본: quotes)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="INFO | DEBUG",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="active_symbols 기반 동적 구독 모드 사용",
    )
    parser.add_argument(
        "--active-set",
        default=None,
        help="동적 구독 시 사용할 Redis Set 이름 (기본: active_symbols)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        help="active_symbols 폴링 주기(초)",
    )
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    settings = Settings(provider=Provider(args.provider), symbols=parse_symbols(args.symbols))

    if args.channel:
        if settings.provider == Provider.upbit:
            settings.upbit.channel = args.channel
        elif settings.provider == Provider.binance:
            settings.binance.channel = args.channel

    # 환경변수 REDIS_URL/REDIS_CHANNEL을 사용해 stdout 전환 또는 채널 설정을 덮어쓴다.
    env_redis_url = os.getenv("REDIS_URL")
    if env_redis_url is not None:
        settings.redis.url = env_redis_url
    env_redis_channel = os.getenv("REDIS_CHANNEL")
    if env_redis_channel:
        settings.redis.channel = env_redis_channel

    # env 값과 args 값이 둘 다 존재하면 args 값을 우선 적용
    if args.redis_url:
        settings.redis.url = args.redis_url
    if args.redis_channel:
        settings.redis.channel = args.redis_channel
    if args.log_level:
        settings.common.log_level = args.log_level.upper()

    # 동적 구독 옵션: args 로 값을 덮어씀 (args 우선)
    env_dynamic = os.getenv("DYNAMIC_ENABLED")
    if env_dynamic is not None:
        settings.dynamic.enabled = env_dynamic.lower() in ("1", "true", "yes")
    if args.dynamic:
        settings.dynamic.enabled = True

    env_active_set = os.getenv("ACTIVE_SYMBOL_SET")
    if env_active_set:
        settings.dynamic.active_set = env_active_set
    if args.active_set:
        settings.dynamic.active_set = args.active_set

    env_poll = os.getenv("ACTIVE_SYMBOL_POLL_INTERVAL")
    if env_poll:
        try:
            settings.dynamic.poll_interval_s = float(env_poll)
        except ValueError:
            pass
    if args.poll_interval:
        settings.dynamic.poll_interval_s = args.poll_interval

    configure_logging(settings.common.log_level)
    logging.getLogger(__name__).info(
        "Starting market data ingestor provider=%s symbols=%s channel=%s dynamic=%s",
        settings.provider.value,
        settings.symbols,
        args.channel or "default",
        settings.dynamic.enabled,
    )

    sink = build_sink(settings)
    if settings.dynamic.enabled:
        await manage_dynamic_ingestor(settings, sink)
    else:
        if not settings.symbols:
            raise ValueError("symbols must be provided when dynamic mode is disabled")
        ingestor = build_ingestor(settings, sink)
        await ingestor.run_forever()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Interrupted, exiting...")


if __name__ == "__main__":
    main()
