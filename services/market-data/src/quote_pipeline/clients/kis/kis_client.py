"""KIS client - KIS WebSocket 클라이언트."""

import logging
from typing import Iterable, Optional, Set

import websockets

from quote_pipeline.clients.base_client import BaseClient
from quote_pipeline.clients.kis.kis_config import (
    KisConfig,
    KisTrType,
    build_subscription,
)
from quote_pipeline.clients.kis.kis_auth_client import KisWsAuthClient
from quote_pipeline.clients.kis.kis_ws_client import KisWsClient
from quote_pipeline.services.subscription_service import SubscriptionService
from quote_pipeline.utils.trading_hours import infer_market_from_symbol

logger = logging.getLogger(__name__)


class KisClient(BaseClient):
    """
    KIS WebSocket 클라이언트.

    KIS OpenAPI WebSocket과의 연결 및 구독 관리를 담당합니다.
    기존 KisAdapter의 WebSocket lifecycle 로직을 유지합니다.
    """

    def __init__(
        self,
        config: KisConfig,
        auth_client: KisWsAuthClient,
        subscription_service: SubscriptionService,
        exchange: str = "NAS",
    ):
        """
        KisClient 초기화.

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
            logger.warning("[KisClient] Already connected")
            return

        # Approval Key 발급
        logger.info("[KisClient] Issuing approval key...")
        self.ws_client.issue_approval_key()
        logger.info("[KisClient] Approval key issued successfully")

        # WebSocket 연결
        # 참고: KIS는 다중연결 시 도메인에 직접 연결하고, TR_ID는 구독 메시지에서 지정
        uri = self.ws_client.cfg.ws_base_url
        logger.info("[KisClient] Connecting to WebSocket: %s", uri)

        self.ws = await websockets.connect(uri, ping_interval=30)
        logger.info("[KisClient] WebSocket connected successfully")

    async def subscribe(self, symbols: Iterable[str]) -> None:
        """
        심볼 구독을 등록합니다.

        Args:
            symbols: 구독할 심볼 리스트
        """
        if not self.ws:
            raise RuntimeError("[KisClient] Not connected. Call connect() first.")

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
        logger.info("[KisClient] _subscribe_symbol: symbol=%s, inferred_market=%s", symbol, market)

        sub = build_subscription(symbol, market, self.exchange)
        logger.info(
            "[KisClient] Built subscription: tr_id=%s, tr_key=%s, symbol=%s",
            sub.tr_id, sub.tr_key, sub.symbol
        )

        # 이미 구독 중이면 스킵
        if self.subscription_service.is_subscribed(sub.tr_id, symbol):
            logger.debug("[KisClient] Already subscribed: %s (%s)", symbol, sub.tr_id)
            return

        # 구독 메시지 전송
        req = self.ws_client._build_ws_message(sub.tr_id, sub.tr_key, KisTrType.REGISTER)
        logger.info("[KisClient] Sending subscribe request: %s", req)
        await self.ws.send(req)

        # 구독 상태 기록
        self.subscription_service.mark_subscribed(sub.tr_id, symbol, sub.tr_key)
        logger.info("[KisClient][%s] Subscribed %s (%s)", sub.tr_id, symbol, sub.tr_key)

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
            raise RuntimeError("[KisClient] Not connected. Call connect() first.")

        msg = await self.ws.recv()
        logger.debug("[KisClient] Received message (len=%d): %s", len(msg), msg[:200] if len(msg) > 200 else msg)
        return msg  # type: ignore

    async def close(self) -> None:
        """
        WebSocket 연결을 종료합니다.
        """
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.subscription_service.clear()
            logger.info("[KisClient] Connection closed")

    async def apply_symbols(self, symbols: Iterable[str]) -> None:
        """
        동적으로 구독 심볼을 변경합니다.

        WebSocket 재연결 없이 구독 목록을 변경합니다.
        기존 KisAdapter.apply_symbols() 로직을 유지합니다.

        Args:
            symbols: 새로운 구독 심볼 리스트
        """
        if not self.ws:
            raise RuntimeError("[KisClient] Not connected. Call connect() first.")

        self.desired_symbols = set(symbols)

        # 원하는 구독 목록 생성: (tr_id, symbol) -> tr_key
        desired_subs = {}
        for sym in self.desired_symbols:
            market = infer_market_from_symbol(sym)
            sub = build_subscription(sym, market, self.exchange)
            desired_subs[(sub.tr_id, sym)] = sub.tr_key

        # 구독 변경사항 계산
        to_add, to_remove = self.subscription_service.calculate_changes(desired_subs)

        if to_add or to_remove:
            logger.info("[KisClient] Apply: add=%d remove=%d", len(to_add), len(to_remove))

        # 구독 해제
        for (tr_id, sym), tr_key in to_remove.items():
            req = self.ws_client._build_ws_message(tr_id, tr_key, KisTrType.UNREGISTER)
            await self.ws.send(req)
            self.subscription_service.mark_unsubscribed(tr_id, sym)
            logger.info("[KisClient][%s] Unsubscribed %s (%s)", tr_id, sym, tr_key)

        # 구독 등록
        for (tr_id, sym), tr_key in to_add.items():
            req = self.ws_client._build_ws_message(tr_id, tr_key, KisTrType.REGISTER)
            await self.ws.send(req)
            self.subscription_service.mark_subscribed(tr_id, sym, tr_key)
            logger.info("[KisClient][%s] Subscribed %s (%s)", tr_id, sym, tr_key)
