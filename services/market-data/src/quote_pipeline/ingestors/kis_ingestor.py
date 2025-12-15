import asyncio
import contextlib
import json
import logging
from typing import Any, Dict, Iterable, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed

from quote_pipeline.ingestors.clients.kis.kis_auth import KisWsAuthClient
from quote_pipeline.ingestors.clients.kis.kis_config import KisConfig
from quote_pipeline.ingestors.clients.kis.kis_ws import KisWsClient
from quote_pipeline.sinks import Sink
from quote_pipeline.utils.trading_hours import infer_market_from_symbol

logger = logging.getLogger(__name__)


# =============================================================================
# KIS 해외주식 실시간 체결가 파싱 (HDFSCNT0)
# =============================================================================
# 데이터 형식: "0|HDFSCNT0|001|{data}"
# data 형식: ^ 구분자로 분리된 필드들
# 필드 순서 (0-indexed):
#   0: RSYM (실시간종목코드, 예: DNASNVDA)
#   1: SYMB (종목코드, 예: NVDA)
#   2: ZDIV (소수점자리수)
#   3: TYMD (현지영업일자)
#   4: XYMD (현지일자)
#   5: XHMS (현지시간)
#   6: KYMD (한국일자)
#   7: KHMS (한국시간)
#   8: OPEN (시가)
#   9: HIGH (고가)
#  10: LOW (저가)
#  11: LAST (현재가)
#  12: SIGN (대비구분)
#  13: DIFF (전일대비)
#  14: RATE (등락율)
#  15: PBID (매수호가)
#  16: PASK (매도호가)
#  17: VBID (매수잔량)
#  18: VASK (매도잔량)
#  19: EVOL (체결량)
#  20: TVOL (거래량)
#  21: TAMT (거래대금)
#  22: BIVL (매수체결량)
#  23: APTS (매도체결량)
#  24: SPTS (52주최고가)
#  25: ... (추가 필드)


def parse_overseas_realtime(raw_msg: str) -> Optional[Dict[str, Any]]:
    """
    해외주식 실시간 체결가 메시지를 파싱한다.

    Args:
        raw_msg: "0|HDFSCNT0|001|DNASNVDA^NVDA^..." 형태의 원본 메시지

    Returns:
        파싱된 payload dict 또는 None
    """
    try:
        # "|" 로 분리: [암호화여부, TR_ID, 건수, 데이터]
        parts = raw_msg.split("|")
        if len(parts) < 4:
            return None

        data_part = parts[3]
        fields = data_part.split("^")

        if len(fields) < 21:
            logger.debug("[kis][overseas] Not enough fields: %d", len(fields))
            return None

        rsym = fields[0]  # DNASNVDA
        symbol = fields[1]  # NVDA
        zdiv = int(fields[2]) if fields[2] else 0  # 소수점 자리수

        # 거래소 코드 추출 (RSYM에서 D + 3자리 거래소코드 + 심볼)
        # 예: DNASNVDA → NAS
        exchange = rsym[1:4] if len(rsym) > 4 else "NAS"

        # 가격 필드 파싱 (소수점 자리수 적용)
        def parse_price(val: str) -> Optional[float]:
            if not val:
                return None
            try:
                return float(val)
            except ValueError:
                return None

        return {
            "symbol": symbol,
            "national": "US",  # 기본값, 추후 거래소별로 분기 가능
            "market": exchange,
            "price": parse_price(fields[11]),  # LAST (현재가)
            "open": parse_price(fields[8]),  # OPEN
            "high": parse_price(fields[9]),  # HIGH
            "low": parse_price(fields[10]),  # LOW
            "change": parse_price(fields[13]),  # DIFF (전일대비)
            "change_rate": parse_price(fields[14]),  # RATE (등락율)
            "volume": parse_price(fields[20]),  # TVOL (거래량)
            "timestamp": f"{fields[6]}{fields[7]}",  # KYMD + KHMS (한국시간)
        }
    except Exception as e:
        logger.debug("[kis][overseas] Parse error: %s", e)
        return None


def parse_domestic_realtime(raw_msg: str) -> Optional[Dict[str, Any]]:
    """
    국내주식 실시간 체결가 메시지를 파싱한다.
    TODO: 추후 구현

    Args:
        raw_msg: 원본 메시지

    Returns:
        파싱된 payload dict 또는 None
    """
    # 국내주식은 JSON 형태로 오는 경우와 pipe 형태로 오는 경우가 있음
    # 추후 실제 데이터 형식 확인 후 구현
    return None


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
        payload: Dict[str, Any] = {"provider": "kis", "tr_id": self.tr_id, "raw": msg}

        if self.tr_id == "HDFSCNT0":
            # 해외주식 실시간 체결가 파싱
            parsed = parse_overseas_realtime(msg)
            if parsed:
                payload["data"] = parsed
            else:
                # 파싱 실패 시 JSON 시도 (구독 응답 등)
                self._try_parse_json_response(msg, payload)
        elif self.tr_id == "H0UNCNT0":
            # 국내주식 실시간 체결가 파싱
            parsed = parse_domestic_realtime(msg)
            if parsed:
                payload["data"] = parsed
            else:
                # 파싱 실패 시 JSON 시도
                self._try_parse_json_response(msg, payload)
                # national/market 기본값 설정 (data가 없는 경우)
                if "data" not in payload:
                    payload["data"] = {}
                if "national" not in payload.get("data", {}):
                    payload["data"]["national"] = "KR"
                if "market" not in payload.get("data", {}) and payload.get("data", {}).get("symbol"):
                    payload["data"]["market"] = KisIngestor._symbol_market_cache.get(
                        payload["data"]["symbol"], "KRX"
                    )
        else:
            # 기타 TR_ID
            self._try_parse_json_response(msg, payload)

        await self.sink.publish(payload)

    def _try_parse_json_response(self, msg: str, payload: Dict[str, Any]) -> None:
        """JSON 형식의 응답 메시지 파싱 시도 (구독 응답 등)."""
        try:
            json_data = json.loads(msg)
            if isinstance(json_data, dict):
                header = json_data.get("header", {})
                body = json_data.get("body", {})
                symbol = header.get("tr_key") or body.get("tr_key")

                output = body.get("output") if isinstance(body, dict) else None

                # data 구조로 통합
                parsed: Dict[str, Any] = {}
                if symbol:
                    parsed["symbol"] = symbol
                if isinstance(output, dict):
                    price = output.get("last") or output.get("tp") or output.get("price")
                    volume = output.get("vol") or output.get("tvol")
                    if price is not None:
                        parsed["price"] = price
                    if volume is not None:
                        parsed["volume"] = volume

                if parsed:
                    payload["data"] = parsed
                payload["raw"] = json_data
        except json.JSONDecodeError:
            pass  # JSON이 아닌 경우 무시


class KisIngestor:
    """
    KIS openapi 직접 사용한 WS 인게스터 (TR_ID별 멀티 세션).
    국내(H0UNCNT0) / 해외(HDFSCNT0)를 별도 세션으로 유지하며 동적으로 심볼을 추가/삭제한다.
    """

    # 심볼 → 마켓 캐시 (DB 조회 결과 저장)
    _symbol_market_cache: Dict[str, str] = {}

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
        # 캐시 로드 (DB에서 심볼 → 마켓 매핑)
        await self._load_symbol_market_cache()
        # 초기 심볼 반영
        await self.apply_symbols(self.desired_symbols)
        # 단순 슬립 루프로 생명 유지 (세션은 개별 태스크로 동작)
        while True:
            await asyncio.sleep(3600)

    async def _load_symbol_market_cache(self) -> None:
        """DB에서 심볼 → 마켓 매핑을 캐시에 로드."""
        try:
            from quote_pipeline.db import get_db

            db = get_db()
            rows = await db.fetch(
                "SELECT symbol, market FROM securities_master WHERE national = 'KR'"
            )
            for row in rows:
                KisIngestor._symbol_market_cache[row["symbol"]] = row["market"]
            logger.info(
                "[kis] Loaded %d symbols into market cache", len(KisIngestor._symbol_market_cache)
            )
        except Exception:
            logger.warning("[kis] Failed to load symbol market cache from DB", exc_info=True)

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
