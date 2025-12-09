import os
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables (including .env if present) once at import time
load_dotenv()


class Provider(str, Enum):
    upbit = "upbit"
    binance = "binance"
    kis = "kis"


class RedisConfig(BaseModel):
    url: Optional[str] = Field(
        default=None, description="redis://localhost:6379/0 형식. 미설정 시 stdout sink 사용"
    )
    channel: str = Field(default="quotes", description="발행할 Redis Pub/Sub 채널명")


class CommonConfig(BaseModel):
    log_level: str = Field(default="INFO")
    reconnect_base_delay: float = Field(default=1.0, description="초 단위 백오프 시작값")
    reconnect_max_delay: float = Field(default=20.0, description="초 단위 백오프 최대값")


class DynamicConfig(BaseModel):
    enabled: bool = Field(default=False, description="active_symbols 기반 동적 구독 사용 여부")
    active_set: str = Field(default="active_symbols", description="Redis Set 이름")
    poll_interval_s: float = Field(default=5.0, description="active_symbols 폴링 주기(초)")


class UpbitConfig(BaseModel):
    url: str = Field(default="wss://api.upbit.com/websocket/v1")
    channel: str = Field(default="ticker", description="ticker | trade | orderbook")
    is_only_realtime: bool = Field(default=True)


class BinanceConfig(BaseModel):
    url: str = Field(default="wss://stream.binance.com:9443/stream")
    channel: str = Field(default="trade", description="trade | ticker(bookTicker) 등")


class KisConfig(BaseModel):
    id: Optional[str] = Field(
        default_factory=lambda: os.getenv("KIS_ID"), description="HTS 로그인 ID (env: KIS_ID)"
    )
    account: Optional[str] = Field(
        default_factory=lambda: os.getenv("KIS_ACCOUNT"), description="계좌번호 (env: KIS_ACCOUNT)"
    )
    appkey: Optional[str] = Field(
        default_factory=lambda: os.getenv("KIS_APP_KEY"), description="AppKey (env: KIS_APP_KEY)"
    )
    secretkey: Optional[str] = Field(
        default_factory=lambda: os.getenv("KIS_APP_SECRET"),
        description="SecretKey (env: KIS_APP_SECRET)",
    )


class Settings(BaseModel):
    provider: Provider = Provider.upbit
    symbols: List[str] = Field(default_factory=list)
    upbit: UpbitConfig = Field(default_factory=UpbitConfig)
    binance: BinanceConfig = Field(default_factory=BinanceConfig)
    kis: KisConfig = Field(default_factory=KisConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    common: CommonConfig = Field(default_factory=CommonConfig)
    dynamic: DynamicConfig = Field(default_factory=DynamicConfig)
