import os
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables (including .env if present) once at import time
load_dotenv()

# Cache environment variables to avoid 반복 os.getenv 호출
ENV_PROVIDERS = os.getenv("PROVIDERS")
ENV_SYMBOLS = os.getenv("SYMBOLS")
ENV_CHANNEL = os.getenv("CHANNEL")
ENV_REDIS_URL = os.getenv("REDIS_URL")
ENV_REDIS_CHANNEL = os.getenv("REDIS_CHANNEL")
ENV_LOG_LEVEL = os.getenv("LOGGING_LEVEL")
ENV_DYNAMIC_ENABLED = os.getenv("DYNAMIC_ENABLED")
ENV_ACTIVE_SET = os.getenv("ACTIVE_SYMBOL_SET")
ENV_ACTIVE_POLL = os.getenv("ACTIVE_SYMBOL_POLL_INTERVAL")
ENV_CHANNEL_UPBIT = os.getenv("CHANNEL_UPBIT")
ENV_CHANNEL_BINANCE = os.getenv("CHANNEL_BINANCE")
ENV_CHANNEL_KIS = os.getenv("CHANNEL_KIS")
ENV_KIS_ID = os.getenv("KIS_ID")
ENV_KIS_ACCOUNT = os.getenv("KIS_ACCOUNT")
ENV_KIS_APP_KEY = os.getenv("KIS_APP_KEY")
ENV_KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")


def parse_symbols(symbols_str: str) -> List[str]:
    """콤마로 구분된 심볼 문자열을 리스트로 변환한다."""
    return [s.strip() for s in symbols_str.split(",") if s.strip()]


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
        default=ENV_KIS_ID, description="HTS 로그인 ID (env: KIS_ID)"
    )
    account: Optional[str] = Field(
        default=ENV_KIS_ACCOUNT, description="계좌번호 (env: KIS_ACCOUNT)"
    )
    appkey: Optional[str] = Field(
        default=ENV_KIS_APP_KEY, description="AppKey (env: KIS_APP_KEY)"
    )
    secretkey: Optional[str] = Field(
        default=ENV_KIS_APP_SECRET, description="SecretKey (env: KIS_APP_SECRET)"
    )
    channel: str = Field(default="price", description="KIS 실시간 채널 식별자 (옵션)")


class Settings(BaseModel):
    providers: List[Provider] = Field(default_factory=list, description="provider 리스트 (1개면 single, 여러개면 multi)")
    symbols: List[str] = Field(default_factory=list)
    upbit: UpbitConfig = Field(default_factory=UpbitConfig)
    binance: BinanceConfig = Field(default_factory=BinanceConfig)
    kis: KisConfig = Field(default_factory=KisConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    common: CommonConfig = Field(default_factory=CommonConfig)
    dynamic: DynamicConfig = Field(default_factory=DynamicConfig)


def build_settings_from_args(args) -> Settings:
    """
    CLI args + 환경변수(.env 포함)를 한곳에서 병합한다.
    우선순위: CLI args > 환경변수 > 기본값
    """
    providers_val = getattr(args, "providers", None) or ENV_PROVIDERS
    symbols_val = getattr(args, "symbols", None) or ENV_SYMBOLS or ""

    # 채널 override (거래소별)
    common_channel = getattr(args, "channel", None) or ENV_CHANNEL
    channel_upbit = getattr(args, "channel_upbit", None) or ENV_CHANNEL_UPBIT or common_channel
    channel_binance = getattr(args, "channel_binance", None) or ENV_CHANNEL_BINANCE or common_channel
    channel_kis = getattr(args, "channel_kis", None) or ENV_CHANNEL_KIS or common_channel

    # Redis 설정
    redis_url_val = getattr(args, "redis_url", None) or ENV_REDIS_URL
    redis_channel_val = getattr(args, "redis_channel", None) or ENV_REDIS_CHANNEL

    # 로그 레벨
    log_level_val = getattr(args, "log_level", None) or ENV_LOG_LEVEL

    # 동적 구독 옵션
    dynamic_enabled = False
    if ENV_DYNAMIC_ENABLED is not None:
        dynamic_enabled = ENV_DYNAMIC_ENABLED.lower() in ("1", "true", "yes")
    if getattr(args, "dynamic", False):
        dynamic_enabled = True

    active_set_val = getattr(args, "active_set", None) or ENV_ACTIVE_SET
    poll_val_raw = getattr(args, "poll_interval", None) or ENV_ACTIVE_POLL
    poll_val = None
    if poll_val_raw:
        try:
            poll_val = float(poll_val_raw)
        except ValueError:
            poll_val = None

    # providers 파싱 (콤마 구분, 1개면 single / 여러개면 multi)
    providers_list: List[Provider] = []
    if providers_val:
        providers_list = [Provider(p.strip()) for p in providers_val.split(",") if p.strip()]

    # Settings 생성
    settings = Settings(
        providers=providers_list,
        symbols=parse_symbols(symbols_val),
    )

    if channel_upbit:
        settings.upbit.channel = channel_upbit
    if channel_binance:
        settings.binance.channel = channel_binance
    if channel_kis:
        settings.kis.channel = channel_kis

    if redis_url_val is not None:
        settings.redis.url = redis_url_val
    if redis_channel_val:
        settings.redis.channel = redis_channel_val

    if log_level_val:
        settings.common.log_level = log_level_val

    settings.dynamic.enabled = dynamic_enabled
    if active_set_val:
        settings.dynamic.active_set = active_set_val
    if poll_val is not None:
        settings.dynamic.poll_interval_s = poll_val

    return settings
