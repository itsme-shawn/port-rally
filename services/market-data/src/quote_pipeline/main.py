import argparse
import asyncio
import logging

from quote_pipeline.db import get_db
from quote_pipeline.config import build_settings_from_args
from quote_pipeline.logging_config import configure_logging
from quote_pipeline.ingestors import IngestorFactory, IngestorManager

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


async def init_redis(settings, redis_client) -> None:
    """
    기존 active_symbols Set 및 quote Hash를 초기화하고 심볼을 seed.

    심볼 분류는 단순 규칙 기반:
    - KRW- 로 시작: upbit
    - usdt로 끝남 (소문자): binance
    - 나머지: kis (미국 주식)
    """
    # 1. 기존 provider별 active_symbols Set 초기화
    for provider in settings.providers:
        provider_set = f"{settings.dynamic.active_set}:{provider.value}"
        deleted = await redis_client.delete(provider_set)
        if deleted:
            logger.info("Cleared existing Redis Set: %s", provider_set)

    # 2. 기존 quote Hash 키 초기화
    quote_keys = await redis_client.keys("quote:*")
    if quote_keys:
        deleted_count = await redis_client.delete(*quote_keys)
        logger.info("Cleared %d existing quote keys", deleted_count)

    # 3. 심볼이 있으면 분류 후 seed (단순 규칙 기반)
    if not settings.symbols:
        logger.info("No symbols to seed, starting with empty active_symbols")
        return

    from quote_pipeline.config import Provider

    classified = {provider: set() for provider in settings.providers}

    for symbol in settings.symbols:
        sym_upper = symbol.upper()
        sym_lower = symbol.lower()

        if sym_upper.startswith("KRW-"):
            if Provider.upbit in classified:
                # Upbit는 대문자 코드 사용
                classified[Provider.upbit].add(sym_upper)
        elif sym_lower.endswith("usdt") or sym_lower.endswith("btc"):
            if Provider.binance in classified:
                classified[Provider.binance].add(symbol)
        else:
            # 기본값: kis (미국 주식)
            if Provider.kis in classified:
                classified[Provider.kis].add(symbol)

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

    # Publisher 생성 (새 아키텍처)
    publisher = IngestorFactory.build_publisher(settings)
    store = IngestorFactory.build_store(settings)

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

        # Redis 초기화 (active_symbols + quote 키) + 심볼 자동 분류 및 seed
        await init_redis(settings, redis_client)

    # Database 연결 생성 (심볼 캐시 로드용)
    db = get_db()

    # Master Loader 초기 실행을 먼저 완료 (startup load)
    # 이후 scheduled 실행은 백그라운드 태스크로 실행
    from quote_pipeline.loader.scheduler import run_master_loader_with_retry
    logger.info("[Main] Running initial master loader (startup)...")
    await run_master_loader_with_retry("startup")
    logger.info("[Main] Initial master loader completed")

    # IngestorManager로 실행 (새 아키텍처)
    # 이제 SymbolService가 완전한 DB에서 캐시를 로드할 수 있음
    manager = IngestorManager(
        settings=settings,
        publisher=publisher,
        db_pool=db,
        redis_client=redis_client,
    )

    # Scheduled master loader를 백그라운드로 실행
    # Redis를 공유 캐시로 사용하므로, master_loader가 DB 업데이트 후
    # Redis에 다시 로드하면 모든 프로세스가 자동으로 최신 데이터를 사용합니다
    async def scheduled_loader():
        """정기적인 master loader 실행 (startup 제외)"""
        from quote_pipeline.loader.scheduler import (
            _next_run_time,
            run_master_loader_with_retry,
            SCHEDULE_TZ,
        )
        from datetime import datetime

        while True:
            now = datetime.now(SCHEDULE_TZ)
            next_run = _next_run_time(now)
            delay = max(0.0, (next_run - now).total_seconds())
            logger.info(
                "[MasterLoaderScheduler] Next run at %s (in %.1fs)",
                next_run.isoformat(),
                delay,
            )
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                logger.info("[MasterLoaderScheduler] Scheduler cancelled")
                raise

            # master_loader 실행
            await run_master_loader_with_retry("scheduled")

            # TODO: scheduled 업데이트 후 Redis에 메타데이터 다시 로드
            # 현재는 startup 시에만 Redis에 로드하고 있음
            logger.info("[MasterLoaderScheduler] Scheduled load completed")

    # FastAPI 서버 설정 및 백그라운드 실행
    from fastapi import FastAPI
    from quote_pipeline.api.router import router, init_api_clients
    import uvicorn

    app = FastAPI(title="PortRally Market Data API")
    app.include_router(router)
    init_api_clients(settings)

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level=settings.common.log_level.lower())
    server = uvicorn.Server(config)

    async def run_api_server():
        try:
            await server.serve()
        except asyncio.CancelledError:
            logger.info("[API] Server task cancelled")

    api_server_task = asyncio.create_task(run_api_server())
    master_loader_task = asyncio.create_task(scheduled_loader())
    store_task = None
    try:
        # QuoteStore는 Redis Pub/Sub → Hash 저장용 사이드카. Redis URL 없으면 비활성화.
        if store:
            store_task = asyncio.create_task(store.start())

        # 4가지 모드 선택
        is_multi = len(settings.providers) > 1
        is_dynamic = settings.dynamic.enabled

        if is_multi and is_dynamic:
            await manager.run_multi_provider_dynamic_symbol()
        elif is_multi and not is_dynamic:
            await manager.run_multi_provider_static_symbol()
        elif not is_multi and is_dynamic:
            await manager.run_single_provider_dynamic_symbol()
        else:
            await manager.run_single_provider_static_symbol()
    finally:
        if store_task:
            store_task.cancel()
            try:
                await store_task
            except asyncio.CancelledError:
                pass
        if master_loader_task:
            master_loader_task.cancel()
            try:
                await master_loader_task
            except asyncio.CancelledError:
                pass
        if api_server_task:
            server.should_exit = True
            api_server_task.cancel()
            try:
                await api_server_task
            except asyncio.CancelledError:
                pass


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Interrupted, exiting...")


if __name__ == "__main__":
    main()
