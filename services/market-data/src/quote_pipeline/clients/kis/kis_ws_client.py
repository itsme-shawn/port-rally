import json
import logging
from typing import Iterable, Tuple

import websockets

from quote_pipeline.clients.kis.kis_config import (
    KisConfig,
    KisTrId,
    KisTrType,
    KisSubscription,
    get_ws_endpoint,
)
from quote_pipeline.clients.kis.kis_auth_client import KisWsAuthClient

logger = logging.getLogger(__name__)


class KisWsClient:
    """
    한투 웹소켓 실시간(H0UNCNT0, HDFSASP0) 구독용 클라이언트.
    KisRestClient와 동일하게 KisConfig, KisAuthClient를 주입하는 방식으로 작성.
    """

    def __init__(self, config: KisConfig, auth_client: KisWsAuthClient):
        self.cfg = config
        self.auth = auth_client
        # 웹소켓 접속용 approval_key
        self.approval_key: str | None = None

    # ---------------------------------------------------------
    # 1) 실시간(WebSocket) 접속키 발급: /oauth2/Approval
    # ---------------------------------------------------------
    def issue_approval_key(self) -> str:
        """승인키 발급/캐시를 KisWsAuthClient에 위임."""
        self.approval_key = self.auth.get_valid_approval_key()
        logger.info("approval_key issued via KisWsAuthClient: %s", self.approval_key)
        return self.approval_key

    # ---------------------------------------------------------
    # 내부용: WS 메시지 생성
    # ---------------------------------------------------------
    def _build_ws_message(self, tr_id: str, tr_key: str, tr_type: str = "1") -> str:
        """
        tr_type:
            - "1" : 등록
            - "2" : 해제
        """
        if not self.approval_key:
            raise RuntimeError("approval_key 가 없습니다. issue_approval_key() 먼저 호출.")

        msg = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": tr_type,
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": tr_key,
                }
            },
        }
        return json.dumps(msg)

    # ---------------------------------------------------------
    # 국내주식 실시간 체결가(통합) H0UNCNT0
    # ---------------------------------------------------------
    async def subscribe_domestic_ticks(
        self,
        symbols: Iterable[str],
        message_handler=None,
    ):
        """
        국내주식 실시간 체결가(통합)
        TR_ID = H0UNCNT0
        """
        symbols = list(symbols)
        tr_id = KisTrId.DOMESTIC_TICK.value
        uri = f"{self.cfg.ws_base_url}{get_ws_endpoint(tr_id)}"
        logger.info(
            "Connecting domestic WS: uri=%s, symbols=%s, approval_key_cached=%s",
            uri,
            symbols,
            bool(self.approval_key),
        )
        if not self.approval_key:
            self.issue_approval_key()

        try:
            async with websockets.connect(uri, ping_interval=30) as ws:
                logger.info("Connected to domestic WS: %s", uri)

                # 등록
                for code in symbols:
                    sub = KisSubscription.for_domestic(code)
                    req = self._build_ws_message(sub.tr_id, sub.tr_key, KisTrType.REGISTER)
                    await ws.send(req)
                    logger.info("sent register domestic: %s", code)

                # 수신 루프
                while True:
                    msg = await ws.recv()
                    if message_handler:
                        message_handler(msg)
                    else:
                        print("DOMESTIC:", msg)
        except Exception:
            logger.exception("Domestic WS connect or receive failed: uri=%s", uri)
            raise

    # ---------------------------------------------------------
    # 해외주식 실시간(지연)체결가[실시간-007] HDFSCNT0
    # ---------------------------------------------------------
    async def subscribe_overseas_askbid(
        self,
        items: Iterable[Tuple[str, str]],
        message_handler=None,
    ):
        """
        해외주식 실시간 체결가
        TR_ID = HDFSCNT0
        tr_key = D{EXCD}{SYMB}

        items = [(EXCD, SYMB), ...]
        """
        items = list(items)
        tr_id = KisTrId.OVERSEAS_TICK.value
        uri = f"{self.cfg.ws_base_url}{get_ws_endpoint(tr_id)}"
        logger.info(
            "Connecting overseas WS: uri=%s, items=%s, approval_key_cached=%s",
            uri,
            items,
            bool(self.approval_key),
        )
        if not self.approval_key:
            self.issue_approval_key()

        try:
            async with websockets.connect(uri, ping_interval=30) as ws:
                logger.info("Connected to overseas WS: %s", uri)

                # 등록
                for exch, symb in items:
                    sub = KisSubscription.for_overseas(symb, exch)
                    req = self._build_ws_message(sub.tr_id, sub.tr_key, KisTrType.REGISTER)
                    await ws.send(req)
                    logger.info("sent register overseas: %s", sub.tr_key)

                # 수신 루프
                while True:
                    msg = await ws.recv()
                    if message_handler:
                        message_handler(msg)
                    else:
                        print("OVERSEAS:", msg)
        except Exception:
            logger.exception("Overseas WS connect or receive failed: uri=%s", uri)
            raise

    # ---------------------------------------------------------
    # 단일 심볼 테스트용: 승인키 발급 후 바로 구독
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # 단일 심볼 테스트용: subscribe_* 래퍼
    # ---------------------------------------------------------
    async def stream_once(
        self,
        market: str,
        symbol: str,
        exch: str | None = None,
    ):
        """
        단일 심볼 구독 테스트용 헬퍼.

        - 내부적으로 이미 정의된 subscribe_domestic_ticks / subscribe_overseas_askbid 를 호출
        - 결과는 웹소켓 수신 메시지를 그대로 print 하는 handler 로 출력
        - 사용 예:
            await ws_client.stream_once("domestic", "005930")
            await ws_client.stream_once("overseas", "TSLA", exch="NAS")
        """

        def _print_handler(msg: str) -> None:
            # subscribe_* 쪽에서 raw str을 넘겨주고 있으니 그대로 출력
            logger.info("WS recv: %s", msg)
            print(msg)

        market = market.lower()
        logger.info(
            "stream_once start: market=%s, symbol=%s, exch=%s, approval_key_cached=%s",
            market,
            symbol,
            exch,
            bool(self.approval_key),
        )

        if market in ("domestic", "kr", "korea"):
            # 국내: 단일 심볼만 리스트로 래핑해서 전달
            await self.subscribe_domestic_ticks(
                symbols=[symbol],
                message_handler=_print_handler,
            )

        elif market in ("overseas", "global", "us", "foreign"):
            if not exch:
                raise ValueError("해외 종목 구독 시 exch(NYS/NAS 등) 파라미터가 필요합니다.")
            await self.subscribe_overseas_askbid(
                items=[(exch, symbol)],
                message_handler=_print_handler,
            )

        else:
            raise ValueError(f"unknown market: {market}")

    # ---------------------------------------------------------
    # 동적 추가/제거 API (단일 WebSocket 세션 안에서 수행)
    # ---------------------------------------------------------
    async def register_symbol(self, ws, tr_id: str, tr_key: str):
        req = self._build_ws_message(tr_id, tr_key, tr_type="1")
        await ws.send(req)

    async def unregister_symbol(self, ws, tr_id: str, tr_key: str):
        req = self._build_ws_message(tr_id, tr_key, tr_type="2")
        await ws.send(req)
