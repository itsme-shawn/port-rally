import asyncio
import contextlib
import json
import logging
from decimal import Decimal
from typing import Any, List

from datetime import datetime, time, timedelta
from pathlib import Path
import os

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
        redis_url: str | None = None,
        active_set: str | None = None,
    ) -> None:
        self.symbols = symbols
        self.sink = sink
        self.user_id = user_id
        self.account = account
        self.appkey = appkey
        self.secretkey = secretkey
        self.redis_url = redis_url
        self.active_set = active_set
        self.tickets: dict[str, Any] = {}
        self.loop: asyncio.AbstractEventLoop | None = None
        self.kis: PyKis | None = None
        self.redis_client = None

    async def run_forever(self) -> None:
        load_dotenv()
        self.loop = asyncio.get_running_loop()
        if not all([self.user_id, self.account, self.appkey, self.secretkey]):
            raise ValueError("KIS credentials (id, account, appkey, secretkey) are required.")

        # 토큰 파일 없이 바로 PyKis 초기화
        self.kis = PyKis(
            id=self.user_id,
            account=self.account,
            appkey=self.appkey,
            secretkey=self.secretkey,
            keep_token=True,
        )

        # redis 클라이언트 (동기화용)
        if self.redis_url:
            try:
                import redis.asyncio as redis  # type: ignore

                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                logger.info("KIS Redis sync enabled url=%s active_set=%s", self.redis_url, self.active_set)
            except Exception as err:
                logger.warning("KIS Redis sync init failed (%s). Continuing without sync.", err)
                self.redis_client = None

        def ensure_market_open(sym: str) -> bool:
            market = infer_market_from_symbol(sym)
            market_code = "KR" if market == "KR" else "US"
            try:
                is_open = is_market_open(lambda: self.kis.trading_hours(market_code))  # type: ignore[arg-type]
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

        async def subscribe_symbol(sym: str) -> None:
            try:
                ticket = self.kis.stock(sym).on(  # type: ignore[call-arg]
                    event="price", 
                    callback=on_price, 
                    extended=True
                )
                self.tickets[sym] = ticket
                logger.info("KIS subscribed to %s", sym)
            except Exception as err:
                logger.error("KIS subscribe failed for %s: %s", sym, err)
                if self.redis_client and self.active_set:
                    await self.redis_client.srem(self.active_set, sym)

        async def unsubscribe_symbol(sym: str) -> None:
            ticket = self.tickets.pop(sym, None)
            if ticket:
                try:
                    ticket.unsubscribe()
                    logger.info("KIS unsubscribed from %s", sym)
                except Exception as err:
                    logger.error("KIS unsubscribe failed for %s: %s", sym, err)

        async def apply_symbols(target_symbols: set[str]) -> None:
            current = set(self.tickets.keys())
            to_add = target_symbols - current
            to_remove = current - target_symbols
            logger.info("KIS apply_symbols add=%s remove=%s", to_add, to_remove)

            for sym in to_remove:
                await unsubscribe_symbol(sym)
            for sym in to_add:
                await subscribe_symbol(sym)
            self.symbols = list(target_symbols)
            logger.info("KIS Active subscriptions: %s", self.kis.websocket.subscriptions)  # type: ignore[attr-defined]

        # 외부에서 심볼 세트를 동기화할 수 있도록 메서드로 노출
        self.apply_symbols = apply_symbols  # type: ignore[assignment]

        # 초기 심볼 반영
        await apply_symbols(set(self.symbols))

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            with contextlib.suppress(Exception):
                # 세션 충돌을 방지하기 위해 웹소켓을 명시적으로 종료
                if self.kis:
                    self.kis.websocket.stop()  # type: ignore[attr-defined]
            for sym, t in list(self.tickets.items()):
                with contextlib.suppress(Exception):
                    if t:
                        t.unsubscribe()
                self.tickets.pop(sym, None)
            if self.redis_client:
                with contextlib.suppress(Exception):
                    await self.redis_client.aclose()
            logger.info("Symbols [%s] Ingestor stopped.", self.symbols)
