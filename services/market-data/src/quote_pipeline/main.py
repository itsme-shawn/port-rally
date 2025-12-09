import argparse
import asyncio
import logging

from quote_pipeline.config import Provider, build_settings_from_args
from quote_pipeline.logging_config import configure_logging
from quote_pipeline.pipeline import build_ingestor, build_sink
from quote_pipeline.active_symbols import manage_dynamic_ingestor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PortRally market-data")
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
        "--channel-upbit",
        default=None,
        help="Upbit 전용 채널 override (ticker/trade/orderbook)",
    )
    parser.add_argument(
        "--channel-binance",
        default=None,
        help="Binance 전용 채널 override (trade/bookTicker 등)",
    )
    parser.add_argument(
        "--channel-kis",
        default=None,
        help="KIS 전용 채널 override (옵션)",
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
    settings = build_settings_from_args(args)

    configure_logging(settings.common.log_level)
    channel_label = "default"
    if settings.provider == Provider.upbit:
        channel_label = settings.upbit.channel
    elif settings.provider == Provider.binance:
        channel_label = settings.binance.channel
    elif settings.provider == Provider.kis:
        channel_label = settings.kis.channel

    logging.getLogger(__name__).info(
        "Starting market data ingestor provider=%s symbols=%s channel=%s dynamic=%s",
        settings.provider.value,
        settings.symbols,
        channel_label,
        settings.dynamic.enabled,
    )

    # 추후 삭제 필요
    logging.getLogger(__name__).info("Effective settings:\n%s", settings.model_dump_json(indent=2, ensure_ascii=False))

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
