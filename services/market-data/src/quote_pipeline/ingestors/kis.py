import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, List

from datetime import datetime, time, timedelta

from dotenv import load_dotenv
from pykis import KisSubscriptionEventArgs, KisWebsocketClient, PyKis
from requests import ConnectionError as RequestsConnectionError

from quote_pipeline.sinks import Sink
from quote_pipeline.utils.trading_hours import infer_market_from_symbol, is_market_open

logger = logging.getLogger(__name__)


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
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

        def ensure_market_open(sym: str) -> bool:
            market = infer_market_from_symbol(sym)
            market_code = "KR" if market == "KR" else "US"
            try:
                is_open = is_market_open(lambda: kis.trading_hours(market_code))
                if not is_open:
                    logger.warning(
                        "KIS [%s] market closed . Skipping subscription for %s.", market_code, sym
                    )
                    return False
                logger.info("KIS [%s] market open . Proceeding subscription for %s.", market_code, sym)
                return True
            except Exception as err:
                logger.error("Failed to fetch trading hours (%s): %s", market_code, err)
                return False

        def on_price(sender: KisWebsocketClient, e: KisSubscriptionEventArgs):
            payload = {
                "provider": "kis",
                "symbol": getattr(e.response, "symbol", None) or getattr(e.response, "code", None),
                "price": getattr(e.response, "price", None),
                "time": getattr(e.response, "time", None),
                # stringify raw to avoid nested datetime/Decimal serialization issues (kis_realtime style)
                "raw": str(e.response),
            }
            safe_payload = _to_jsonable(payload)
            if not self.loop:
                logger.error("Event loop is not set; dropping message")
                return
            fut = asyncio.run_coroutine_threadsafe(self.sink.publish(safe_payload), self.loop)

            def _cb(f):
                if exc := f.exception():
                    logger.error("KIS sink publish failed: %s", exc)

            fut.add_done_callback(_cb)

        for sym in self.symbols:
            try:
                if not ensure_market_open(sym):
                    continue
                ticket = kis.stock(sym).on("price", on_price)
                self.tickets.append(ticket)
                logger.info("KIS subscribed to %s", sym)
            except Exception as err:
                logger.error("KIS subscribe failed for %s: %s", sym, err)

        logger.info("KIS Active subscriptions: %s", kis.websocket.subscriptions)

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            for t in self.tickets:
                t.unsubscribe()
