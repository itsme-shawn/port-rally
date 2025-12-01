import logging

from quote_pipeline.config import Provider, Settings
from quote_pipeline.ingestors.binance import BinanceIngestor
from quote_pipeline.ingestors.upbit import UpbitIngestor
from quote_pipeline.sinks import RedisSink, Sink, StdoutSink

logger = logging.getLogger(__name__)


def build_sink(settings: Settings) -> Sink:
    if settings.redis.url:
        logger.info("Using Redis sink url=%s channel=%s", settings.redis.url, settings.redis.channel)
        return RedisSink(url=settings.redis.url, channel=settings.redis.channel)
    # redis 설정 안 되어있으면 stdout 로 출력
    logger.info("Using Stdout sink")
    return StdoutSink()


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
    raise ValueError(f"Unsupported provider: {settings.provider}")
