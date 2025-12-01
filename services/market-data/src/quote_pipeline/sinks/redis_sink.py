import json
import logging
from typing import Any, Dict, Optional

from .base import Sink

logger = logging.getLogger(__name__)


class RedisSink(Sink):
    def __init__(self, url: str, channel: str = "quotes") -> None:
        try:
            import redis.asyncio as redis  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError("redis package not installed") from exc
        self._redis = redis.from_url(url, decode_responses=True)
        self.channel = channel

    async def publish(self, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False)
        try:
            await self._redis.publish(self.channel, encoded)
        except Exception:
            logger.exception("Failed to publish to Redis channel=%s", self.channel)
            raise
