import logging
import os

from quote_pipeline.config import Provider, Settings
from quote_pipeline.ingestors.binance import BinanceIngestor
from quote_pipeline.ingestors.kis import KisIngestor
from quote_pipeline.ingestors.upbit import UpbitIngestor
from quote_pipeline.sinks import RedisSink, Sink, StdoutSink

logger = logging.getLogger(__name__)


def build_sink(settings: Settings) -> Sink:
    # env 우선 적용 (run 시 -e REDIS_URL=stdout 등)
    env_url = os.getenv("REDIS_URL")
    if env_url is not None:
        settings.redis.url = env_url
    url = settings.redis.url or ""
    sentinel = ("", "null", "none", "stdout")
    if url.strip().lower() in sentinel:
        logger.info("Using Stdout sink")
        return StdoutSink()
    logger.info("Using Redis sink url=%s channel=%s", url, settings.redis.channel)
    return RedisSink(url=url, channel=settings.redis.channel)


def build_ingestor(settings: Settings, sink: Sink):
    common_kwargs = {
        "sink": sink,
        "reconnect_base_delay": settings.common.reconnect_base_delay,
        "reconnect_max_delay": settings.common.reconnect_max_delay,
    }

    if settings.provider == Provider.upbit:
        return UpbitIngestor(
            symbols=settings.symbols,
            channel=settings.upbit.channel,
            is_only_realtime=settings.upbit.is_only_realtime,
            url=settings.upbit.url,
            **common_kwargs,
        )
    if settings.provider == Provider.binance:
        return BinanceIngestor(
            symbols=settings.symbols,
            channel=settings.binance.channel,
            url=settings.binance.url,
            **common_kwargs,
        )
    if settings.provider == Provider.kis:
        return KisIngestor(
            symbols=settings.symbols,
            user_id=settings.kis.id,
            account=settings.kis.account,
            appkey=settings.kis.appkey,
            secretkey=settings.kis.secretkey,
            sink=sink,
        )
    raise ValueError(f"Unsupported provider: {settings.provider}")
