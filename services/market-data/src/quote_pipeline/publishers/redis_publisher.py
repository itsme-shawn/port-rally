"""Redis publisher - Redis Pub/Sub 발행자."""

import json
import logging
from typing import Any, Dict

from quote_pipeline.publishers.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class RedisPublisher(BasePublisher):
    """
    Redis Pub/Sub 발행자.

    Redis 채널에 메시지를 발행합니다.
    """

    def __init__(self, url: str, channel: str = "quotes") -> None:
        """
        RedisPublisher 초기화.

        Args:
            url: Redis 연결 URL
            channel: 발행할 채널 이름
        """
        try:
            import redis.asyncio as redis  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError("redis package not installed") from exc
        self._redis = redis.from_url(url, decode_responses=True)
        self.channel = channel

    async def publish(self, payload: Dict[str, Any]) -> None:
        """
        Redis 채널에 메시지를 발행합니다.

        Args:
            payload: 발행할 데이터 (JSON 직렬화 가능)
        """
        encoded = json.dumps(payload, ensure_ascii=False)
        try:
            await self._redis.publish(self.channel, encoded)
        except Exception:
            logger.exception("Failed to publish to Redis channel=%s", self.channel)
            raise
