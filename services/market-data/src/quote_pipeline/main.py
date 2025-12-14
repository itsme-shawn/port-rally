import argparse
import asyncio
import logging

from quote_pipeline.config import build_settings_from_args
from quote_pipeline.logging_config import configure_logging
from quote_pipeline.pipeline import build_sink
from quote_pipeline.ingestors.helper.manage_ingestor import run_ingestor

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PortRally market-data")
    parser.add_argument(
        "--providers",
        help="콤마로 구분된 provider 리스트 (예: kis / kis,upbit,binance). 1개면 single, 여러개면 multi.",
    )
    parser.add_argument(
        "--symbols",
        help="콤마로 구분된 심볼 리스트 (예: KRW-BTC,KRW-ETH / btcusdt,ethusdt / NVDA). 미지정 시 빈 리스트.",
    )
    parser.add_argument(
        "--channel",
        help="채널 override (upbit: ticker/trade/orderbook, binance: trade/bookTicker 등)",
    )
    parser.add_argument(
        "--channel-upbit",
        help="Upbit 전용 채널 override (ticker/trade/orderbook)",
    )
    parser.add_argument(
        "--channel-binance",
        help="Binance 전용 채널 override (trade/bookTicker 등)",
    )
    parser.add_argument(
        "--channel-kis",
        help="KIS 전용 채널 override (옵션)",
    )
    parser.add_argument(
        "--redis-url",
        help="Redis sink URL. 미지정 시 stdout sink 사용",
    )
    parser.add_argument(
        "--redis-channel",
        help="Redis Pub/Sub 채널명 (기본: quotes)",
    )
    parser.add_argument(
        "--log-level",
        help="INFO | DEBUG",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="active_symbols 기반 동적 구독 모드 사용",
    )
    parser.add_argument(
        "--active-set",
        help="동적 구독 시 사용할 Redis Set 이름 (기본: active_symbols)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        help="active_symbols 폴링 주기(초)",
    )
    return parser.parse_args()


async def init_redis_active_symbols(settings, redis_client) -> None:
    """기존 active_symbols Set을 초기화하고 심볼을 DB 기반으로 분류하여 seed."""
    from quote_pipeline.loaders.symbol_resolver import classify_symbols_by_provider

    # 1. 기존 provider별 Set 초기화
    for provider in settings.providers:
        provider_set = f"{settings.dynamic.active_set}:{provider.value}"
        deleted = await redis_client.delete(provider_set)
        if deleted:
            logger.info("Cleared existing Redis Set: %s", provider_set)

    # 2. 심볼이 있으면 분류 후 seed
    if not settings.symbols:
        logger.info("No symbols to seed, starting with empty active_symbols")
        return

    classified = await classify_symbols_by_provider(settings.symbols)

    for provider, symbols in classified.items():
        if symbols:
            provider_set = f"{settings.dynamic.active_set}:{provider.value}"
            await redis_client.sadd(provider_set, *symbols)
            logger.info("Seeded %s with %s", provider_set, symbols)


async def run() -> None:
    args = parse_args()
    settings = build_settings_from_args(args)

    configure_logging(settings.common.log_level)

    # 로깅
    providers_str = ",".join(p.value for p in settings.providers) if settings.providers else "none"
    is_multi = len(settings.providers) > 1
    mode = f"{'multi' if is_multi else 'single'}_{'dynamic' if settings.dynamic.enabled else 'static'}"

    logger.info(
        "Starting market data ingestor mode=%s providers=%s symbols=%s",
        mode,
        providers_str,
        settings.symbols,
    )
    logger.debug("Effective settings:\n%s", settings.model_dump_json(indent=2, ensure_ascii=False))

    # Validation
    if not settings.providers:
        raise ValueError("At least one provider must be specified (--providers or PROVIDERS env)")

    if not settings.dynamic.enabled and not settings.symbols:
        raise ValueError("symbols must be provided when dynamic mode is disabled")

    # Sink 생성
    sink = build_sink(settings)

    # Redis 클라이언트 (동적 심볼 모드(active_symbols)에서만 필요)
    redis_client = None
    if settings.dynamic.enabled:
        try:
            import redis.asyncio as redis
        except ImportError as exc:
            raise RuntimeError("redis package required for dynamic mode") from exc

        if not settings.redis.url:
            raise RuntimeError("dynamic mode requires REDIS_URL")

        redis_client = redis.from_url(settings.redis.url, decode_responses=True)

        # 기존 Set 초기화 + 심볼 자동 분류 및 seed
        await init_redis_active_symbols(settings, redis_client)

    # 통합 진입점으로 실행
    await run_ingestor(settings, sink, redis_client)


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Interrupted, exiting...")


if __name__ == "__main__":
    main()
