import logging
import os

from quote_pipeline.config import Provider, Settings
from quote_pipeline.ingestors.binance_ingestor import BinanceIngestor
from quote_pipeline.ingestors.kis_ingestor import KisIngestor
from quote_pipeline.ingestors.upbit_ingestor import UpbitIngestor
from quote_pipeline.sinks import RedisSink, Sink, StdoutSink

logger = logging.getLogger(__name__)


def build_sink(settings: Settings) -> Sink:
    # env 우선 적용 (run 시 -e REDIS_URL=stdout 등)
    url = settings.redis.url or ""
    sentinel = ("", "null", "none", "stdout")
    if url.strip().lower() in sentinel:
        logger.info("Using Stdout sink")
        return StdoutSink()
    logger.info("Using Redis sink url=%s channel=%s", url, settings.redis.channel)
    return RedisSink(url=url, channel=settings.redis.channel)


def build_ingestor(settings: Settings, provider: Provider, sink: Sink):
    """
    provider에 해당하는 Ingestor 인스턴스를 생성한다.

    Args:
        settings: 파이프라인 설정 (symbols, configs 등)
        provider: 생성할 ingestor의 provider 타입
        sink: 출력 Sink
    """
    common_kwargs = {
        "sink": sink,
        "reconnect_base_delay": settings.common.reconnect_base_delay,
        "reconnect_max_delay": settings.common.reconnect_max_delay,
    }

    if provider == Provider.upbit:
        return UpbitIngestor(
            symbols=settings.symbols,
            channel=settings.upbit.channel,
            is_only_realtime=settings.upbit.is_only_realtime,
            url=settings.upbit.url,
            **common_kwargs,
        )
    if provider == Provider.binance:
        return BinanceIngestor(
            symbols=settings.symbols,
            channel=settings.binance.channel,
            url=settings.binance.url,
            **common_kwargs,
        )
    if provider == Provider.kis:
        return KisIngestor(
            symbols=settings.symbols,
            sink=sink,
            appkey=settings.kis.appkey,
            appsecret=settings.kis.secretkey,
            reconnect_base_delay=settings.common.reconnect_base_delay,
            reconnect_max_delay=settings.common.reconnect_max_delay,
        )
    raise ValueError(f"Unsupported provider: {provider}")
