import json
from typing import Any, Dict, List, Optional

from quote_pipeline.ingestors.base_ingestor import BaseWebSocketIngestor


class UpbitIngestor(BaseWebSocketIngestor):
    @property
    def name(self) -> str:
        return "upbit"

    def __init__(
        self,
        symbols: List[str],
        channel: str,
        sink,
        is_only_realtime: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(url=kwargs.pop("url"), sink=sink, **kwargs)
        self.symbols = symbols
        self.channel = channel
        self.is_only_realtime = is_only_realtime

    def build_subscription_payload(self) -> Any:
        return [
            {"ticket": "port-rally-poc"},
            {
                "type": self.channel,
                "codes": self.symbols,
                "isOnlyRealtime": self.is_only_realtime,
            },
        ]

    def parse_message(self, message: Any) -> Optional[Dict[str, Any]]:
        if isinstance(message, (bytes, bytearray)):
            message = message.decode("utf-8")
        data = json.loads(message)
        return {
            "provider": self.name,
            "symbol": data.get("code"),
            "type": data.get("type"),
            "price": data.get("trade_price"),
            "volume": data.get("trade_volume"),
            "timestamp": data.get("timestamp") or data.get("trade_timestamp"),
            "raw": data,
        }
