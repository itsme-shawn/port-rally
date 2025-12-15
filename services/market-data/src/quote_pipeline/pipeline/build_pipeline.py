"""Build pipeline - Publisher 및 Store 생성 유틸리티."""

import logging
from typing import Optional

from quote_pipeline.config import Settings
from quote_pipeline.publishers.base_publisher import BasePublisher
from quote_pipeline.publishers.redis_publisher import RedisPublisher
from quote_pipeline.publishers.stdout_publisher import StdoutPublisher
from quote_pipeline.stores import QuoteStore

logger = logging.getLogger(__name__)


def build_publisher(settings: Settings) -> BasePublisher:
    """
    Settings에 따라 적절한 Publisher를 생성합니다.

    Args:
        settings: 파이프라인 설정

    Returns:
        BasePublisher 인스턴스 (RedisPublisher 또는 StdoutPublisher)
    """
    # env 우선 적용 (run 시 -e REDIS_URL=stdout 등)
    url = settings.redis.url or ""
    sentinel = ("", "null", "none", "stdout")
    if url.strip().lower() in sentinel:
        logger.info("Using StdoutPublisher")
        return StdoutPublisher()
    logger.info("Using RedisPublisher url=%s channel=%s", url, settings.redis.channel)
    return RedisPublisher(url=url, channel=settings.redis.channel)




def build_store(settings: Settings) -> Optional[QuoteStore]:
    """
    Redis URL이 설정된 경우 QuoteStore 인스턴스를 생성한다.

    Args:
        settings: 파이프라인 설정

    Returns:
        QuoteStore 인스턴스 또는 None (Redis URL 미설정 시)
    """
    url = settings.redis.url or ""
    sentinel = ("", "null", "none", "stdout")
    if url.strip().lower() in sentinel:
        logger.info("QuoteStore disabled (no Redis URL)")
        return None

    store = QuoteStore(
        redis_url=url,
        channel=settings.redis.channel,
        key_prefix="quote",
    )
    logger.info("Built QuoteStore: channel=%s", settings.redis.channel)
    return store
