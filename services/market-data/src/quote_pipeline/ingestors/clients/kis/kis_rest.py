# kis_rest.py
import requests
from quote_pipeline.ingestors.clients.kis.kis_config import KisConfig
from quote_pipeline.ingestors.clients.kis.kis_auth import KisRestAuthClient
import logging

logger = logging.getLogger(__name__)


class KisRestClient:
    def __init__(self, config: KisConfig, auth_client: KisRestAuthClient):
        self.cfg = config
        self.auth = auth_client

    def _auth_header(self, tr_id: str, custtype: str = "P") -> dict:
        """
        tr_id(거래ID), custtype(고객 타입) 받아서 내부용 헤더 생성
        auth 값들은 KisAuthClient가 관리하는 access_token을 사용
        """
        token = self.auth.get_valid_access_token()
        token_type = self.auth._access.token_type if self.auth._access else "Bearer"

        # 디버깅용 로그
        exp = self.auth._expires_at
        if exp:
            from datetime import datetime
            logging.getLogger(__name__).debug(
                "Using access_token exp=%s now=%s", exp, datetime.utcnow()
            )

        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"{token_type} {token}",
            "appkey": self.cfg.app_key,
            "appsecret": self.cfg.app_secret,
            "tr_id": tr_id,
            "custtype": custtype,
        }

    def get_domestic_price(self, code: str, market_div: str = "J") -> dict:
        """
        FHKST01010300 - 주식현재가 체결
        Query:
          - FID_COND_MRKT_DIV_CODE: J(거래소: KRX), NX(NXT), UN(통합)
          - FID_INPUT_ISCD: 종목코드 (단축코드 6자리)
        """
        url = f"{self.cfg.base_url}/uapi/domestic-stock/v1/quotations/inquire-ccnl"

        headers = self._auth_header(tr_id="FHKST01010300", custtype="P")
        params = {
            "FID_COND_MRKT_DIV_CODE": market_div,
            "FID_INPUT_ISCD": code,
        }

        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def get_overseas_price_detail(self, exch_code: str, symbol: str, auth: str = "") -> dict:
        """
        HHDFS00000300 - 해외주식 현재체결가
        Query:
          - AUTH: 사용자권한정보 (개인 기본 사용 시 공백 허용)
          - EXCD: 거래소코드 (NAS/BAQ 등)
                HKS : 홍콩
                NYS : 뉴욕
                NAS : 나스닥
                AMS : 아멕스
                TSE : 도쿄
                SHS : 상해
                SZS : 심천
                SHI : 상해지수
                SZI : 심천지수
                HSX : 호치민
                HNX : 하노이
                BAY : 뉴욕(주간)
                BAQ : 나스닥(주간)
                BAA : 아멕스(주간)
          - SYMB: 종목코드 (예: "TSLA")
        """
        url = f"{self.cfg.base_url}/uapi/overseas-price/v1/quotations/price"

        headers = self._auth_header(tr_id="HHDFS00000300", custtype="P")
        params = {
            "AUTH": auth,
            "EXCD": exch_code,
            "SYMB": symbol,
        }

        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
