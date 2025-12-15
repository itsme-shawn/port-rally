"""KIS adapter - KIS WebSocket 어댑터."""

import asyncio
import logging
from typing import Iterable, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed

from quote_pipeline.adapters.base_adapter import BaseAdapter
from quote_pipeline.adapters.kis.kis_config import KisConfig
from quote_pipeline.adapters.kis.kis_auth_client import KisWsAuthClient
from quote_pipeline.adapters.kis.kis_ws_client import KisWsClient
from quote_pipeline.services.subscription_service import SubscriptionService
from quote_pipeline.utils.trading_hours import infer_market_from_symbol

logger = logging.getLogger(__name__)


class KisAdapter(BaseAdapter):
    """
    KIS WebSocket 어댑터.

    KIS OpenAPI WebSocket과의 연결 및 구독 관리를 담당합니다.
    기존 KisIngestor의 WebSocket lifecycle 로직을 추출했습니다.
    """

    def __init__(
        self,
        config: KisConfig,
        auth_client: KisWsAuthClient,
        subscription_service: SubscriptionService,
        exchange: str = "NAS",
    ):
        """
        KisAdapter 초기화.

        Args:
            config: KIS 설정
            auth_client: KIS WebSocket 인증 클라이언트
            subscription_service: 구독 상태 관리 서비스
            exchange: 기본 거래소 코드 (NAS, NYS 등)
        """
        self.config = config
        self.auth_client = auth_client
        self.subscription_service = subscription_service
        self.exchange = exchange

        self.ws_client = KisWsClient(config, auth_client)
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.desired_symbols: Set[str] = set()

    async def connect(self) -> None:
        """
        KIS WebSocket 서버에 연결합니다.

        Approval Key를 발급받아 WebSocket 연결을 수립합니다.
        """
        if self.ws is not None:
            logger.warning("[KisAdapter] Already connected")
            return

        # Approval Key 발급
        self.ws_client.issue_approval_key()

        # WebSocket 연결 (다중연결: 도메인에 직접 연결)
        uri = self.ws_client.cfg.ws_base_url
        logger.info("[KisAdapter] Connecting to %s", uri)

        self.ws = await websockets.connect(uri, ping_interval=30)
        logger.info("[KisAdapter] Connected successfully")

    async def subscribe(self, symbols: Iterable[str]) -> None:
        """
        심볼 구독을 등록합니다.

        Args:
            symbols: 구독할 심볼 리스트
        """
        if not self.ws:
            raise RuntimeError("[KisAdapter] Not connected. Call connect() first.")

        self.desired_symbols = set(symbols)

        for symbol in symbols:
            await self._subscribe_symbol(symbol)

    async def _subscribe_symbol(self, symbol: str) -> None:
        """
        개별 심볼을 구독합니다.

        Args:
            symbol: 구독할 심볼
        """
        market = infer_market_from_symbol(symbol)

        if market == "KR":
            tr_id = "H0STCNT0"  # 국내주식 실시간체결가
            tr_key = symbol
        else:
            tr_id = "HDFSCNT0"  # 해외주식 실시간체결가
            # TODO : symbol 을 보고 DB에서 exchange code 를 가져와야 함
            tr_key = f"D{self.exchange}{symbol}"

        # 이미 구독 중이면 스킵
        if self.subscription_service.is_subscribed(tr_id, symbol):
            logger.debug("[KisAdapter] Already subscribed: %s (%s)", symbol, tr_id)
            return

        # 구독 메시지 전송
        req = self.ws_client._build_ws_message(tr_id, tr_key, tr_type="1")
        await self.ws.send(req)

        # 구독 상태 기록
        self.subscription_service.mark_subscribed(tr_id, symbol, tr_key)
        logger.info("[KisAdapter][%s] Subscribed %s (%s)", tr_id, symbol, tr_key)

    async def receive(self) -> str:
        """
        WebSocket에서 메시지를 수신합니다.

        Returns:
            수신된 raw 메시지

        Raises:
            RuntimeError: 연결되지 않은 경우
            ConnectionClosed: WebSocket 연결이 끊긴 경우
        """
        if not self.ws:
            raise RuntimeError("[KisAdapter] Not connected. Call connect() first.")

        msg = await self.ws.recv()
        return msg  # type: ignore

    async def close(self) -> None:
        """
        WebSocket 연결을 종료합니다.
        """
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.subscription_service.clear()
            logger.info("[KisAdapter] Connection closed")

    async def apply_symbols(self, symbols: Iterable[str]) -> None:
        """
        동적으로 구독 심볼을 변경합니다.

        WebSocket 재연결 없이 구독 목록을 변경합니다.
        기존 KisIngestor.apply_symbols() 로직을 추출했습니다.

        Args:
            symbols: 새로운 구독 심볼 리스트
        """
        if not self.ws:
            raise RuntimeError("[KisAdapter] Not connected. Call connect() first.")

        self.desired_symbols = set(symbols)

        # 원하는 구독 목록 생성: (tr_id, symbol) -> tr_key
        desired_subs = {}
        for sym in self.desired_symbols:
            market = infer_market_from_symbol(sym)
            if market == "KR":
                tr_id = "H0STCNT0"
                tr_key = sym
            else:
                tr_id = "HDFSCNT0"
                tr_key = f"D{self.exchange}{sym}"
            desired_subs[(tr_id, sym)] = tr_key

        # 구독 변경사항 계산
        to_add, to_remove = self.subscription_service.calculate_changes(desired_subs)

        if to_add or to_remove:
            logger.info("[KisAdapter] Apply: add=%d remove=%d", len(to_add), len(to_remove))

        # 구독 해제
        for (tr_id, sym), tr_key in to_remove.items():
            req = self.ws_client._build_ws_message(tr_id, tr_key, tr_type="2")
            await self.ws.send(req)
            self.subscription_service.mark_unsubscribed(tr_id, sym)
            logger.info("[KisAdapter][%s] Unsubscribed %s (%s)", tr_id, sym, tr_key)

        # 구독 등록
        for (tr_id, sym), tr_key in to_add.items():
            req = self.ws_client._build_ws_message(tr_id, tr_key, tr_type="1")
            await self.ws.send(req)
            self.subscription_service.mark_subscribed(tr_id, sym, tr_key)
            logger.info("[KisAdapter][%s] Subscribed %s (%s)", tr_id, sym, tr_key)
