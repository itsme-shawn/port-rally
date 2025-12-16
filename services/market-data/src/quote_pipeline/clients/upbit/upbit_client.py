"""Upbit client - 단순 WebSocket 클라이언트."""

import json
import logging
from typing import Iterable, Optional, Set

import websockets
from websockets import WebSocketClientProtocol

from quote_pipeline.clients.base_client import BaseClient

logger = logging.getLogger(__name__)


class UpbitClient(BaseClient):
    """
    Upbit WebSocket 클라이언트.

    ticker/trade/channel 기반으로 심볼을 구독하고 raw 메시지를 전달한다.
    """

    def __init__(self, url: str, channel: str = "ticker") -> None:
        self.url = url
        self.channel = channel
        self.ws: Optional[WebSocketClientProtocol] = None
        self.symbols: Set[str] = set()

    async def connect(self) -> None:
        if self.ws:
            logger.warning("[UpbitClient] Already connected")
            return
        logger.info("[UpbitClient] Connecting to %s", self.url)
        self.ws = await websockets.connect(self.url, ping_interval=30)
        logger.info("[UpbitClient] Connected")

    async def subscribe(self, symbols: Iterable[str]) -> None:
        if not self.ws:
            raise RuntimeError("[UpbitClient] Not connected. Call connect() first.")

        self.symbols = set(symbols)
        if not self.symbols:
            logger.info("[UpbitClient] No symbols to subscribe")
            return

        payload = [
            {"ticket": "port-rally"},
            {"type": self.channel, "codes": list(self.symbols)},
        ]
        await self.ws.send(json.dumps(payload))
        logger.info("[UpbitClient] Subscribed channel=%s symbols=%s", self.channel, self.symbols)

    async def receive(self) -> str:
        if not self.ws:
            raise RuntimeError("[UpbitClient] Not connected. Call connect() first.")
        msg = await self.ws.recv()
        if isinstance(msg, bytes):
            return msg.decode("utf-8")
        return msg

    async def close(self) -> None:
        if self.ws:
            await self.ws.close()
            self.ws = None
            logger.info("[UpbitClient] Connection closed")

    async def apply_symbols(self, symbols: Iterable[str]) -> None:
        # Upbit는 구독 변경 API가 따로 없으므로 재구독 메시지를 재전송한다.
        await self.subscribe(symbols)
