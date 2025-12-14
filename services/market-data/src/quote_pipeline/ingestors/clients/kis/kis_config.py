# kis_config.py
from dataclasses import dataclass

@dataclass
class KisConfig:
    app_key: str
    app_secret: str          # tokenP, REST에서 사용하는 appsecret
    is_vts: bool = False     # 모의투자 여부

    @property
    def base_url(self) -> str:
        # REST base url
        if self.is_vts:
            return "https://openapivts.koreainvestment.com:29443"
        return "https://openapi.koreainvestment.com:9443"

    @property
    def ws_base_url(self) -> str:
        # WebSocket base url
        return "ws://ops.koreainvestment.com:21000"
