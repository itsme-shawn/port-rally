from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    upbit = "upbit"
    binance = "binance"


class RedisConfig(BaseModel):
    url: Optional[str] = Field(
        default=None, description="redis://localhost:6379/0 형식. 미설정 시 stdout sink 사용"
    )
    channel: str = Field(default="quotes", description="발행할 Redis Pub/Sub 채널명")


class CommonConfig(BaseModel):
    log_level: str = Field(default="INFO")
    reconnect_base_delay: float = Field(default=1.0, description="초 단위 백오프 시작값")
    reconnect_max_delay: float = Field(default=20.0, description="초 단위 백오프 최대값")


class UpbitConfig(BaseModel):
    url: str = Field(default="wss://api.upbit.com/websocket/v1")
    channel: str = Field(default="ticker", description="ticker | trade | orderbook")
    is_only_realtime: bool = Field(default=True)


class BinanceConfig(BaseModel):
    url: str = Field(default="wss://stream.binance.com:9443/stream")
    channel: str = Field(default="trade", description="trade | ticker(bookTicker) 등")


class Settings(BaseModel):
    provider: Provider = Provider.upbit
    symbols: List[str] = Field(default_factory=lambda: ["KRW-BTC"])
    upbit: UpbitConfig = Field(default_factory=UpbitConfig)
    binance: BinanceConfig = Field(default_factory=BinanceConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    common: CommonConfig = Field(default_factory=CommonConfig)
