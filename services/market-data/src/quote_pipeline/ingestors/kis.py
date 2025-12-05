import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, List

from dotenv import load_dotenv
from pykis import KisSubscriptionEventArgs, KisWebsocketClient, PyKis
from requests import ConnectionError as RequestsConnectionError

from quote_pipeline.sinks import Sink

logger = logging.getLogger(__name__)


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "model_dump"):
        dumped = obj.model_dump()
        return {k: _to_jsonable(v) for k, v in dumped.items()}
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


class KisIngestor:
    def __init__(
        self,
        symbols: List[str],
        sink: Sink,
        user_id: str | None = None,
        account: str | None = None,
        appkey: str | None = None,
        secretkey: str | None = None,
    ) -> None:
        self.symbols = symbols
        self.sink = sink
        self.user_id = user_id
        self.account = account
        self.appkey = appkey
        self.secretkey = secretkey
        self.tickets = []
        self.loop: asyncio.AbstractEventLoop | None = None

    async def run_forever(self) -> None:
        load_dotenv()
        self.loop = asyncio.get_running_loop()
        if not all([self.user_id, self.account, self.appkey, self.secretkey]):
            raise ValueError("KIS credentials (id, account, appkey, secretkey) are required.")

        kis = PyKis(
            id=self.user_id,
            account=self.account,
            appkey=self.appkey,
            secretkey=self.secretkey,
            keep_token=True,
        )

        def on_price(sender: KisWebsocketClient, e: KisSubscriptionEventArgs):
            payload = {
                "provider": "kis",
                "symbol": getattr(e.response, "symbol", None) or getattr(e.response, "code", None),
                "price": getattr(e.response, "price", None),
                "time": getattr(e.response, "time", None),
                "raw": _to_jsonable(e.response),
            }
            safe_payload = _to_jsonable(payload)
            if not self.loop:
                logger.error("Event loop is not set; dropping message")
                return
            asyncio.run_coroutine_threadsafe(self.sink.publish(safe_payload), self.loop)

        for sym in self.symbols:
            try:
                ticket = kis.stock(sym).on("price", on_price)
                self.tickets.append(ticket)
            except RequestsConnectionError as err:
                logger.error("KIS subscribe failed for %s: %s", sym, err)

        logger.info("KIS Active subscriptions: %s", kis.websocket.subscriptions)

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            for t in self.tickets:
                t.unsubscribe()
