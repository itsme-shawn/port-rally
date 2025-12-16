"""
QuoteStore: Redis Pub/Sub을 구독하여 현재가를 Redis Hash에 저장.

Key 구조: quote:{market}:{symbol}
Value: Redis Hash (last, volume, timestamp 등)
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class QuoteStore:
    """
    Redis Pub/Sub 채널을 구독하여 수신한 quote 데이터를
    quote:{market}:{symbol} 형태의 Redis Hash로 저장.
    """

    def __init__(
        self,
        redis_url: str,
        channel: str = "quotes",
        key_prefix: str = "quote",
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Args:
            redis_url: Redis 연결 URL (예: redis://localhost:6379/0)
            channel: 구독할 Pub/Sub 채널명
            key_prefix: Hash 키 prefix (기본: "quote")
            ttl_seconds: Hash 키 TTL (None이면 만료 없음)
        """
        self._redis_url = redis_url
        self._channel = channel
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.Redis.pubsub] = None
        self._running = False

    async def start(self) -> None:
        """Pub/Sub 구독을 시작하고 메시지 처리 루프 실행."""
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self._channel)
        self._running = True

        logger.info(
            "[QuoteStore] Started subscribing channel=%s key_prefix=%s",
            self._channel,
            self._key_prefix,
        )

        try:
            await self._consume_loop()
        finally:
            await self.stop()

    async def stop(self) -> None:
        """구독 중지 및 연결 정리."""
        self._running = False
        if self._pubsub:
            await self._pubsub.unsubscribe(self._channel)
            await self._pubsub.close()
            self._pubsub = None
        if self._redis:
            await self._redis.close()
            self._redis = None
        logger.info("[QuoteStore] Stopped")

    async def _consume_loop(self) -> None:
        """Pub/Sub 메시지 수신 루프."""
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message is None:
                    continue

                if message["type"] != "message":
                    continue

                data = message["data"]
                if isinstance(data, str):
                    payload = json.loads(data)
                    await self._handle_message(payload)

            except json.JSONDecodeError as e:
                logger.warning("[QuoteStore] Invalid JSON: %s", e)
            except Exception:
                logger.exception("[QuoteStore] Error processing message")
                await asyncio.sleep(0.1)

    async def _handle_message(self, payload: Dict[str, Any]) -> None:
        """
        수신한 메시지를 Redis Hash로 저장.

        Expected payload (kis):
        {
            "provider": "kis",
            "tr_id": "HDFSCNT0",
            "raw": "...",
            "data": {
                "symbol": "NVDA",
                "market": "NAS",
                "price": 177.74,
                "volume": 123456,
                ...
            }
        }

        Expected payload (upbit/binance):
        {
            "provider": "upbit|binance",
            "market": "UPBIT|BINANCE",
            "symbol": "KRW-BTC|BTCUSDT",
            "price": 72000,
            "volume": 1234,
            ...
        }
        """
        provider = payload.get("provider", "")

        # data 키 구조 지원 (kis)
        data = payload.get("data", {})
        if data:
            symbol = data.get("symbol")
            market = data.get("market")
            price = data.get("price")
            volume = data.get("volume")
            timestamp = data.get("timestamp")
            extra_fields = data
        else:
            # 기존 flat 구조 (upbit, binance)
            symbol = payload.get("symbol")
            market = payload.get("market")
            price = payload.get("price")
            volume = payload.get("volume")
            timestamp = payload.get("timestamp")
            extra_fields = payload

        if not all([symbol, market]):
            logger.debug(
                "[QuoteStore] Missing required fields: symbol=%s market=%s",
                symbol,
                market,
            )
            return

        # Redis Hash 키 생성
        key = f"{self._key_prefix}:{market}:{symbol}"

        # Hash 필드 구성
        hash_fields = {
            "provider": provider,
            "last": str(price) if price is not None else "",
            "volume": str(volume) if volume is not None else "",
            "timestamp": str(timestamp) if timestamp is not None else "",
            "updated_at": str(int(time.time())),
        }

        # 추가 필드 (있으면 저장)
        for field in ("change", "change_rate", "high", "low", "open"):
            val = extra_fields.get(field)
            if val is not None:
                hash_fields[field] = str(val)

        # Redis Hash 저장
        await self._redis.hset(key, mapping=hash_fields)

        # TTL 설정 (선택)
        if self._ttl_seconds:
            await self._redis.expire(key, self._ttl_seconds)

        logger.debug("[QuoteStore] Saved %s: last=%s", key, hash_fields.get("last"))


async def run_quote_store(
    redis_url: str,
    channel: str = "quotes",
    key_prefix: str = "quote",
    ttl_seconds: Optional[int] = None,
) -> None:
    """QuoteStore 실행 헬퍼 함수."""
    store = QuoteStore(
        redis_url=redis_url,
        channel=channel,
        key_prefix=key_prefix,
        ttl_seconds=ttl_seconds,
    )
    await store.start()


if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)

    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ch = os.getenv("REDIS_CHANNEL", "quotes")

    asyncio.run(run_quote_store(redis_url=url, channel=ch))
