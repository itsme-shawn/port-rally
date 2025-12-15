import asyncio
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

        # 거래소 코드 추출 (RSYM에서 D + 3자리 거래소코드 + 심볼)
        # 예: DNASNVDA → NAS
        exchange = rsym[1:4] if len(rsym) > 4 else "NAS"

        # 가격 필드 파싱
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


class KisIngestor:
    """
    KIS openapi WebSocket 인게스터 (다중연결 방식).

    하나의 WebSocket 연결에서 여러 TR_ID(국내/해외)를 동시에 구독한다.
    - 다중연결 시 도메인에 직접 연결 (URL path 없음)
    - 체결(H0STCNT0/HDFSCNT0) + 호가 합쳐서 최대 20개 (향후 60개 확장 예정)

    TR_ID 종류:
    - H0STCNT0: 국내주식 실시간체결가 (tr_key: 종목코드, 예: 005930)
    - H0STASP0: 국내주식 실시간호가
    - HDFSCNT0: 해외주식 실시간체결가 (tr_key: D{거래소}{종목코드}, 예: DNASNVDA)
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

        # 단일 WebSocket 연결
        self.ws = None
        # TR_ID + 심볼 조합으로 구독 상태 관리
        # key: (tr_id, symbol), value: tr_key
        self.subscribed: Dict[tuple, str] = {}

    async def run_forever(self) -> None:
        # 캐시 로드 (DB에서 심볼 → 마켓 매핑)
        await self._load_symbol_market_cache()

        delay = self.reconnect_base_delay
        while True:
            try:
                await self._stream_once()
                delay = self.reconnect_base_delay
            except ConnectionClosed as exc:
                logger.warning(
                    "[kis] websocket closed code=%s reason=%s; retrying in %.1fs",
                    getattr(exc, "code", None),
                    getattr(exc, "reason", None),
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("[kis] stream error, retrying in %.1fs", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)

    async def _stream_once(self) -> None:
        if not self.desired_symbols:
            logger.info("[kis] no symbols; sleeping")
            await asyncio.sleep(1)
            return

        self.ws_client.issue_approval_key()
        # 다중연결: 도메인에 직접 연결 (path 없음)
        uri = self.ws_client.cfg.ws_base_url
        logger.info("[kis] connecting %s symbols=%s", uri, self.desired_symbols)

        async with websockets.connect(uri, ping_interval=30) as ws:
            self.ws = ws
            # 초기 심볼 구독
            await self.apply_symbols(self.desired_symbols)

            try:
                async for msg in ws:
                    await self._handle_message(msg)  # type: ignore
            except ConnectionClosed as exc:
                logger.warning(
                    "[kis] websocket closed inside loop code=%s reason=%s",
                    getattr(exc, "code", None),
                    getattr(exc, "reason", None),
                )
                raise
            finally:
                self.ws = None
                self.subscribed.clear()

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
        """전체 심볼을 시장별로 분류해 구독/해제 처리."""
        self.desired_symbols = set(symbols)

        # 원하는 구독 목록 생성: (tr_id, symbol) -> tr_key
        desired_subs: Dict[tuple, str] = {}
        for sym in self.desired_symbols:
            market = infer_market_from_symbol(sym)
            if market == "KR":
                tr_id = "H0STCNT0"  # 국내주식 실시간체결가
                tr_key = sym
            else:
                tr_id = "HDFSCNT0"  # 해외주식 실시간체결가
                tr_key = f"D{self.exchange}{sym}"
            desired_subs[(tr_id, sym)] = tr_key

        # 현재 구독 vs 원하는 구독 비교
        current_keys = set(self.subscribed.keys())
        desired_keys = set(desired_subs.keys())

        to_add = desired_keys - current_keys
        to_remove = current_keys - desired_keys

        if to_add or to_remove:
            logger.info("[kis] apply: add=%d remove=%d", len(to_add), len(to_remove))

        # 구독 해제
        for key in to_remove:
            tr_id, sym = key
            tr_key = self.subscribed[key]
            await self._send_subscribe(tr_id, tr_key, tr_type="2")
            del self.subscribed[key]
            logger.info("[kis][%s] unsubscribed %s (%s)", tr_id, sym, tr_key)

        # 구독 등록
        for key in to_add:
            tr_id, sym = key
            tr_key = desired_subs[key]
            await self._send_subscribe(tr_id, tr_key, tr_type="1")
            self.subscribed[key] = tr_key
            logger.info("[kis][%s] subscribed %s (%s)", tr_id, sym, tr_key)

    async def _send_subscribe(self, tr_id: str, tr_key: str, tr_type: str) -> None:
        """구독/해제 메시지 전송."""
        if not self.ws:
            return
        req = self.ws_client._build_ws_message(tr_id, tr_key, tr_type=tr_type)
        await self.ws.send(req)

    async def _handle_message(self, msg: str) -> None:
        """수신 메시지 처리."""
        tr_id = self._detect_tr_id(msg)
        payload: Dict[str, Any] = {"provider": "kis", "tr_id": tr_id, "raw": msg}

        if tr_id == "HDFSCNT0":
            # 해외주식 실시간 체결가 파싱
            parsed = parse_overseas_realtime(msg)
            if parsed:
                payload["data"] = parsed
            else:
                self._try_parse_json_response(msg, payload)
        elif tr_id == "H0STCNT0":
            # 국내주식 실시간 체결가 파싱
            parsed = parse_domestic_realtime(msg)
            if parsed:
                payload["data"] = parsed
            else:
                self._try_parse_json_response(msg, payload)
                # national/market 기본값 설정
                if "data" not in payload:
                    payload["data"] = {}
                if "national" not in payload.get("data", {}):
                    payload["data"]["national"] = "KR"
                if "market" not in payload.get("data", {}) and payload.get("data", {}).get("symbol"):
                    payload["data"]["market"] = KisIngestor._symbol_market_cache.get(
                        payload["data"]["symbol"], "KRX"
                    )
        else:
            self._try_parse_json_response(msg, payload)

        await self.sink.publish(payload)

    def _detect_tr_id(self, msg: str) -> str:
        """메시지에서 TR_ID 추출."""
        # 파이프 형식: "0|HDFSCNT0|001|..." 또는 "0|H0STCNT0|001|..."
        if msg.startswith("0|") or msg.startswith("1|"):
            parts = msg.split("|")
            if len(parts) >= 2:
                return parts[1]

        # JSON 형식
        try:
            data = json.loads(msg)
            if isinstance(data, dict):
                header = data.get("header", {})
                return header.get("tr_id", "UNKNOWN")
        except json.JSONDecodeError:
            pass

        return "UNKNOWN"

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
