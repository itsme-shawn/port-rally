import asyncio
import contextlib
import json
import logging
from typing import Dict, Iterable, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed

from quote_pipeline.ingestors.clients.kis.kis_auth import KisWsAuthClient
from quote_pipeline.ingestors.clients.kis.kis_config import KisConfig
from quote_pipeline.ingestors.clients.kis.kis_ws import KisWsClient
from quote_pipeline.sinks import Sink
from quote_pipeline.utils.trading_hours import infer_market_from_symbol

logger = logging.getLogger(__name__)


def _ws_uri(base: str, tr_id: str) -> str:
    mapping = {
        "H0UNCNT0": f"{base}/tryitout/H0UNCNT0",  # 국내 체결
        "HDFSCNT0": f"{base}/tryitout/HDFSCNT0",  # 해외 체결
    }
    return mapping.get(tr_id, f"{base}/tryitout/{tr_id}")


class _TrSession:
    """TR_ID 별 웹소켓 세션을 관리하는 헬퍼."""

    def __init__(
        self,
        tr_id: str,
        ws_client: KisWsClient,
        sink: Sink,
        reconnect_base_delay: float,
        reconnect_max_delay: float,
    ) -> None:
        self.tr_id = tr_id
        self.ws_client = ws_client
        self.sink = sink
        self.reconnect_base_delay = reconnect_base_delay
        self.reconnect_max_delay = reconnect_max_delay

        self.desired: Set[str] = set()
        self.current: Set[str] = set()
        self.ws = None
        self.task: asyncio.Task | None = None

    def start(self) -> None:
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task
            self.task = None

    async def apply_symbols(self, symbols: Set[str]) -> None:
        self.desired = set(symbols)
        if not self.ws:
            logger.info("[kis][%s] pending symbols until ws ready: %s", self.tr_id, self.desired)
            return

        to_add = self.desired - self.current
        to_remove = self.current - self.desired
        logger.info("[kis][%s] apply add=%s remove=%s", self.tr_id, to_add, to_remove)

        for sym in to_remove:
            await self._unregister(sym)
        for sym in to_add:
            await self._register(sym)
        self.current = set(self.desired)

    async def _run_loop(self) -> None:
        delay = self.reconnect_base_delay
        while True:
            try:
                await self._stream_once()
                delay = self.reconnect_base_delay
            except ConnectionClosed as exc:
                logger.warning(
                    "[kis][%s] websocket closed code=%s reason=%s; retrying in %.1fs",
                    self.tr_id,
                    getattr(exc, "code", None),
                    getattr(exc, "reason", None),
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("[kis][%s] stream error, retrying in %.1fs", self.tr_id, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)

    async def _stream_once(self) -> None:
        if not self.desired:
            logger.info("[kis][%s] no symbols; sleeping", self.tr_id)
            await asyncio.sleep(1)
            return

        self.ws_client.issue_approval_key()
        uri = _ws_uri(self.ws_client.cfg.ws_base_url, self.tr_id)
        logger.info("[kis][%s] connecting %s symbols=%s", self.tr_id, uri, self.desired)

        async with websockets.connect(uri, ping_interval=30) as ws:
            self.ws = ws
            # 첫 연결 시 원하는 심볼을 모두 등록
            await self.apply_symbols(self.desired)

            try:
                async for msg in ws:
                    await self._handle_message(msg) # type: ignore
            except ConnectionClosed as exc:
                logger.warning(
                    "[kis][%s] websocket closed inside loop code=%s reason=%s",
                    self.tr_id,
                    getattr(exc, "code", None),
                    getattr(exc, "reason", None),
                )
                raise
            finally:
                self.ws = None
                self.current.clear()

    async def _register(self, sym: str) -> None:
        if not self.ws:
            return
        tr_key = self._tr_key(sym)
        req = self.ws_client._build_ws_message(self.tr_id, tr_key, tr_type="1")
        await self.ws.send(req)
        logger.info("[kis][%s] subscribed %s (%s)", self.tr_id, sym, tr_key)
        self.current.add(sym)

    async def _unregister(self, sym: str) -> None:
        if not self.ws or sym not in self.current:
            return
        tr_key = self._tr_key(sym)
        req = self.ws_client._build_ws_message(self.tr_id, tr_key, tr_type="2")
        await self.ws.send(req)
        logger.info("[kis][%s] unsubscribed %s (%s)", self.tr_id, sym, tr_key)
        self.current.discard(sym)

    def _tr_key(self, sym: str) -> str:
        if self.tr_id == "H0UNCNT0":
            return sym  # 국내 단축코드
        # 해외 체결가: D{EXCD}{SYMB}
        # FIXME : 추후 심볼별 EXCD 매핑 로직 추가해야함
        self.exchange = "NAS"  # 기본 : NASDAQ
        return f"D{self.exchange}{sym}"

    async def _handle_message(self, msg: str) -> None:
        payload = {"provider": "kis", "tr_id": self.tr_id, "raw": msg}
        try:
            data = json.loads(msg)
            if isinstance(data, dict):
                header = data.get("header", {})
                body = data.get("body", {})
                payload["symbol"] = header.get("tr_key") or body.get("tr_key")
                output = body.get("output") if isinstance(body, dict) else None
                if isinstance(output, dict):
                    payload["price"] = output.get("last") or output.get("tp") or output.get("price") # type: ignore
                payload["raw"] = data # type: ignore
        except Exception:
            logger.debug("[kis][%s] parse failed; forwarding raw", self.tr_id)
        await self.sink.publish(payload)


class KisIngestor:
    """
    KIS openapi 직접 사용한 WS 인게스터 (TR_ID별 멀티 세션).
    국내(H0UNCNT0) / 해외(HDFSCNT0)를 별도 세션으로 유지하며 동적으로 심볼을 추가/삭제한다.
    """

    def __init__(
        self,
        symbols: Iterable[str],
        sink: Sink,
        appkey: Optional[str] = None,
        appsecret: Optional[str] = None,
        exchange: str = "NAS",
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 20.0,
    ) -> None:
        if not appkey or not appsecret:
            raise ValueError("KIS appkey/appsecret 이 필요합니다.")

        self.desired_symbols: Set[str] = set(symbols)
        self.sink = sink
        self.exchange = exchange
        self.reconnect_base_delay = reconnect_base_delay
        self.reconnect_max_delay = reconnect_max_delay

        cfg = KisConfig(app_key=appkey, app_secret=appsecret)
        auth = KisWsAuthClient(cfg)
        self.ws_client = KisWsClient(cfg, auth)

        self.sessions: Dict[str, _TrSession] = {}

    async def run_forever(self) -> None:
        # 초기 심볼 반영
        await self.apply_symbols(self.desired_symbols)
        # 단순 슬립 루프로 생명 유지 (세션은 개별 태스크로 동작)
        while True:
            await asyncio.sleep(3600)

    async def apply_symbols(self, symbols: Iterable[str]) -> None:
        """전체 심볼을 시장별로 분리해 TR_ID 세션에 전달."""
        self.desired_symbols = set(symbols)
        tr_map: Dict[str, Set[str]] = {"H0UNCNT0": set(), "HDFSCNT0": set()}

        for sym in self.desired_symbols:
            market = infer_market_from_symbol(sym)
            if market == "KR":
                tr_map["H0UNCNT0"].add(sym)
            else:
                tr_map["HDFSCNT0"].add(sym)

        # 세션 생성/갱신
        for tr_id, sym_set in tr_map.items():
            session = self.sessions.get(tr_id)
            if sym_set:
                if not session:
                    session = _TrSession(
                        tr_id=tr_id,
                        ws_client=self.ws_client,
                        sink=self.sink,
                        reconnect_base_delay=self.reconnect_base_delay,
                        reconnect_max_delay=self.reconnect_max_delay,
                    )
                    self.sessions[tr_id] = session
                    session.start()
                await session.apply_symbols(sym_set)
            else:
                # 심볼이 없으면 세션 종료
                if session:
                    await session.stop()
                    self.sessions.pop(tr_id, None)
