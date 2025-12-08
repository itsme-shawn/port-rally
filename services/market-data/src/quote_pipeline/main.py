import argparse
import asyncio
import logging
from typing import List
import os

from quote_pipeline.config import Provider, Settings
from quote_pipeline.logging_config import configure_logging
from quote_pipeline.pipeline import build_ingestor, build_sink


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
        default="KRW-BTC",
        help="콤마로 구분된 심볼 리스트 (예: KRW-BTC,KRW-ETH / btcusdt,ethusdt / NVDA)",
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
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    settings = Settings(provider=Provider(args.provider), symbols=parse_symbols(args.symbols))

    # KIS 기본 심볼을 지정하지 않은 경우 NVDA로 설정
    if settings.provider == Provider.kis and args.symbols == "KRW-BTC":
        settings.symbols = ["NVDA"]

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

    configure_logging(settings.common.log_level)
    logging.getLogger(__name__).info(
        "Starting market data ingestor provider=%s symbols=%s channel=%s",
        settings.provider.value,
        settings.symbols,
        args.channel or "default",
    )

    sink = build_sink(settings)
    ingestor = build_ingestor(settings, sink)
    await ingestor.run_forever()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Interrupted, exiting...")


if __name__ == "__main__":
    main()
