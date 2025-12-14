import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import websockets
from websockets.legacy.client import WebSocketClientProtocol

from quote_pipeline.sinks import Sink

logger = logging.getLogger(__name__)


class BaseWebSocketIngestor(ABC):
    def __init__(
        self,
        url: str,
        sink: Sink,
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 20.0,
        ping_interval: Optional[float] = 20.0,
        ping_timeout: Optional[float] = 10.0,
    ) -> None:
        self.url = url
        self.sink = sink
        self.reconnect_base_delay = reconnect_base_delay
        self.reconnect_max_delay = reconnect_max_delay
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def build_subscription_payload(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def parse_message(self, message: Any) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def run_forever(self) -> None:
        delay = self.reconnect_base_delay
        while True:
            try:
                await self._stream_once()
                delay = self.reconnect_base_delay
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("[%s] stream error, retrying in %.1fs", self.name, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)

    async def _stream_once(self) -> None:
        logger.info("[%s] connecting to %s", self.name, self.url)
        async with websockets.connect(
            self.url,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            max_queue=None,
        ) as ws:
            await self._subscribe(ws)
            await self._consume(ws)

    async def _subscribe(self, ws: WebSocketClientProtocol) -> None:
        payload = self.build_subscription_payload()
        if payload is not None:
            encoded = json.dumps(payload)
            await ws.send(encoded)
            logger.info("[%s] subscribed with payload=%s", self.name, payload)

    async def _consume(self, ws: WebSocketClientProtocol) -> None:
        async for raw in ws:
            parsed = None
            try:
                parsed = self.parse_message(raw)
            except Exception:
                logger.exception("[%s] failed to parse message", self.name)
                continue

            if parsed is None:
                continue

            parsed["ingested_at"] = time.time()
            try:
                await self.sink.publish(parsed)
            except Exception:
                logger.exception("[%s] sink publish failed", self.name)
                continue
