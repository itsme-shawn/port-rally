import asyncio
import json
import logging
from typing import Iterable, Tuple

import requests
import websockets

from quote_pipeline.ingestors.kis_pure.kis_config import KisConfig
from quote_pipeline.ingestors.kis_pure.kis_auth import KisAuthClient

logger = logging.getLogger(__name__)


class KisWsClient:
    """
    한투 웹소켓 실시간(H0UNCNT0, HDFSASP0) 구독용 클라이언트.
    KisRestClient와 동일하게 KisConfig, KisAuthClient를 주입하는 방식으로 작성.
    """

    def __init__(self, config: KisConfig, auth_client: KisAuthClient):
        self.cfg = config
        self.auth = auth_client

        # 웹소켓 접속용 approval_key
        self.approval_key: str | None = None

    # ---------------------------------------------------------
    # 1) 실시간(WebSocket) 접속키 발급: /oauth2/Approval
    # ---------------------------------------------------------
    def issue_approval_key(self) -> str:
        """
        /oauth2/Approval
        Request Body:
            - grant_type: "client_credentials"
            - appkey
            - secretkey (주의: appsecret 아님)
        Response:
            - approval_key
        """
        url = f"{self.cfg.base_url}/oauth2/Approval"

        payload = {
            "grant_type": "client_credentials",
            "appkey": self.cfg.app_key,
            "secretkey": self.cfg.app_secret,
        }

        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        self.approval_key = data["approval_key"]
        logger.info(f"approval_key issued: {self.approval_key}")
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
        HOST 주소는 KISConfig.ws_domestic_url 사용
        """

        uri = self.cfg.ws_base_url 
        
        
         # ex: ws://ops.koreainvestment.com:21000/tryitout/H0UNCNT0

        if not self.approval_key:
            self.issue_approval_key()

        async with websockets.connect(uri, ping_interval=30) as ws:
            logger.info(f"Connected to domestic WS: {uri}")

            # 등록
            for code in symbols:
                req = self._build_ws_message("H0UNCNT0", code, tr_type="1")
                await ws.send(req)
                logger.info(f"sent register domestic: {code}")

            # 수신 루프
            while True:
                msg = await ws.recv()
                if message_handler:
                    message_handler(msg)
                else:
                    print("DOMESTIC:", msg)

    # ---------------------------------------------------------
    # 해외주식 실시간 호가 HDFSASP0
    # ---------------------------------------------------------
    async def subscribe_overseas_askbid(
        self,
        items: Iterable[Tuple[str, str]],
        message_handler=None,
    ):
        """
        해외주식 실시간 호가
        TR_ID = HDFSASP0
        tr_key = R{EXCD}{SYMB}

        items = [(EXCD, SYMB), ...]
        """

        uri = self.cfg.ws_overseas_askbid_url

        if not self.approval_key:
            self.issue_approval_key()

        async with websockets.connect(uri, ping_interval=30) as ws:
            logger.info(f"Connected to overseas WS: {uri}")

            # 등록
            for exch, symb in items:
                tr_key = f"R{exch}{symb}"
                req = self._build_ws_message("HDFSASP0", tr_key, tr_type="1")
                await ws.send(req)
                logger.info(f"sent register overseas: {tr_key}")

            # 수신 루프
            while True:
                msg = await ws.recv()
                if message_handler:
                    message_handler(msg)
                else:
                    print("OVERSEAS:", msg)

    # ---------------------------------------------------------
    # 동적 추가/제거 API (단일 WebSocket 세션 안에서 수행)
    # ---------------------------------------------------------
    async def register_symbol(self, ws, tr_id: str, tr_key: str):
        req = self._build_ws_message(tr_id, tr_key, tr_type="1")
        await ws.send(req)

    async def unregister_symbol(self, ws, tr_id: str, tr_key: str):
        req = self._build_ws_message(tr_id, tr_key, tr_type="2")
        await ws.send(req)
