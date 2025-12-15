import json
from typing import Any, Dict, List, Optional

from quote_pipeline.ingestors.base_ingestor import BaseWebSocketIngestor


class BinanceIngestor(BaseWebSocketIngestor):
    @property
    def name(self) -> str:
        return "binance"

    def __init__(self, symbols: List[str], channel: str, sink, **kwargs) -> None:
        streams = "/".join(f"{symbol.lower()}@{channel}" for symbol in symbols)
        url = f"{kwargs.pop('url')}?streams={streams}"
        super().__init__(url=url, sink=sink, **kwargs)
        self.channel = channel

    def build_subscription_payload(self) -> Any:
        # Combined stream은 URL에 이미 정의되므로 별도 구독 메시지 불필요
        return None

    def parse_message(self, message: Any) -> Optional[Dict[str, Any]]:
        if isinstance(message, (bytes, bytearray)):
            message = message.decode("utf-8")
        data = json.loads(message)
        payload = data.get("data") or {}
        symbol = payload.get("s") or payload.get("symbol")
        ts = payload.get("T") or payload.get("E")  # trade time 또는 event time

        price = payload.get("p") or payload.get("c")  # trade price or best ask price
        volume = payload.get("q") or payload.get("Q")  # trade qty or best ask qty

        return {
            "provider": self.name,
            "national": "CRYPTO",
            "market": "BINANCE",
            "symbol": symbol,
            "type": self.channel,
            "price": float(price) if price is not None else None,
            "volume": float(volume) if volume is not None else None,
            "timestamp": ts,
            "raw": payload,
        }
