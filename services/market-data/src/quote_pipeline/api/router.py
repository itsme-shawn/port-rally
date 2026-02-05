import logging
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

from quote_pipeline.clients.kis.kis_config import KisConfig
from quote_pipeline.clients.kis.kis_auth_client import KisRestAuthClient
from quote_pipeline.clients.kis.kis_rest_client import KisRestClient
from quote_pipeline.config import Settings
from quote_pipeline.redis_meta import meta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/quotes")
active_symbols_router = APIRouter(prefix="/v1/active-symbols")

PROVIDERS = {"kis", "upbit", "binance"}

# 전역 클라이언트 (서버 시작 시 초기화 권장)
_kis_client: Optional[KisRestClient] = None
_redis_client: Optional[aioredis.Redis] = None


class ActiveSymbolsRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=1, description="추가/삭제할 심볼 목록")


def init_api_clients(settings: Settings):
    global _kis_client, _redis_client
    
    # KIS REST 클라이언트 초기화
    config = KisConfig(
        app_key=settings.kis.appkey,
        app_secret=settings.kis.secretkey,
        is_vts=False
    )
    auth = KisRestAuthClient(config)
    _kis_client = KisRestClient(config, auth)
    logger.info("API Clients (KIS REST) initialized")

    # Redis 클라이언트 초기화
    if settings.redis.url:
        _redis_client = aioredis.from_url(settings.redis.url, decode_responses=True)
        logger.info("API Clients (Redis) initialized")


def _normalize_provider(provider: str) -> str:
    normalized = provider.lower().strip()
    if normalized not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    return normalized


def _normalize_symbols(symbols: list[str]) -> list[str]:
    cleaned = []
    for symbol in symbols:
        if symbol is None:
            continue
        normalized = symbol.strip().upper()
        if normalized:
            cleaned.append(normalized)
    return list(dict.fromkeys(cleaned))


def _require_redis_client() -> aioredis.Redis:
    if not _redis_client:
        raise HTTPException(status_code=503, detail="Redis client not initialized")
    return _redis_client


async def _find_missing_symbol_metadata(
    redis_client: aioredis.Redis,
    symbols: list[str],
) -> list[str]:
    if not symbols:
        return []

    pipe = redis_client.pipeline()
    keys = []
    for symbol in symbols:
        key = meta.symbol_map(symbol=symbol).build()
        keys.append(key)
        pipe.exists(key)

    results = await pipe.execute()
    missing = [symbol for symbol, exists in zip(symbols, results) if not exists]
    return missing


@active_symbols_router.get("/{provider}")
async def list_active_symbols(provider: str):
    """provider별 active_symbols 목록을 조회합니다."""
    normalized_provider = _normalize_provider(provider)
    redis_client = _require_redis_client()
    key = meta.active_symbols(provider=normalized_provider).build()
    symbols = await redis_client.smembers(key)
    sorted_symbols = sorted(symbols) if symbols else []
    return {
        "provider": normalized_provider,
        "symbols": sorted_symbols,
        "count": len(sorted_symbols),
    }


@active_symbols_router.post("/{provider}")
async def add_active_symbols(provider: str, request: ActiveSymbolsRequest):
    """active_symbols에 심볼을 추가합니다."""
    normalized_provider = _normalize_provider(provider)
    symbols = _normalize_symbols(request.symbols)
    if not symbols:
        raise HTTPException(status_code=400, detail="No valid symbols provided")
    redis_client = _require_redis_client()
    key = meta.active_symbols(provider=normalized_provider).build()
    before_count = await redis_client.scard(key)
    added = await redis_client.sadd(key, *symbols)
    after_count = await redis_client.scard(key)
    logger.info(
        "[ActiveSymbols API] add provider=%s key=%s symbols=%s",
        normalized_provider,
        key,
        symbols,
    )
    logger.info(
        "[ActiveSymbols API] add result key=%s before=%d after=%d added=%d",
        key,
        before_count,
        after_count,
        added,
    )

    missing_metadata = await _find_missing_symbol_metadata(redis_client, symbols)
    if missing_metadata:
        logger.warning(
            "[ActiveSymbols API] missing symbol_map entries: %s",
            missing_metadata,
        )
    return {
        "provider": normalized_provider,
        "symbols": symbols,
        "added": added,
    }


@active_symbols_router.delete("/{provider}")
async def remove_active_symbols(
    provider: str,
    symbols: list[str] = Query(..., description="삭제할 심볼 목록"),
):
    """active_symbols에서 심볼을 삭제합니다."""
    normalized_provider = _normalize_provider(provider)
    normalized_symbols = _normalize_symbols(symbols)
    if not normalized_symbols:
        raise HTTPException(status_code=400, detail="No valid symbols provided")
    redis_client = _require_redis_client()
    key = meta.active_symbols(provider=normalized_provider).build()
    before_count = await redis_client.scard(key)
    removed = await redis_client.srem(key, *normalized_symbols)
    after_count = await redis_client.scard(key)
    logger.info(
        "[ActiveSymbols API] remove provider=%s key=%s symbols=%s",
        normalized_provider,
        key,
        normalized_symbols,
    )
    logger.info(
        "[ActiveSymbols API] remove result key=%s before=%d after=%d removed=%d",
        key,
        before_count,
        after_count,
        removed,
    )
    return {
        "provider": normalized_provider,
        "symbols": normalized_symbols,
        "removed": removed,
    }


@router.get("/spot")
async def get_spot_price(
    symbol: str = Query(..., description="종목 코드 (예: 005930)"),
    national: str = Query("KR", description="국가 코드 (KR, US 등)"),
    market: Optional[str] = Query(None, description="거래소 코드 (KOSPI, KOSDAQ, NAS 등)")
):
    """
    특정 종목의 현재가(Spot Price)를 KIS REST API를 통해 즉시 조회하고,
    Redis Active Symbols에 추가하며, 조회 결과를 캐싱합니다.
    """
    if not _kis_client:
        raise HTTPException(status_code=503, detail="KIS client not initialized")

    try:
        # 1. Active Symbols에 추가 (Redis가 연결되어 있다면)
        if _redis_client:
            # 주식은 기본적으로 kis provider로 가정
            active_key = meta.active_symbols(provider="kis").build()
            await _redis_client.sadd(active_key, symbol)
            logger.info(f"Added {symbol} to active_symbols:kis")

        result_data = {}
        quote_key = None

        if national == "KR":
            # 국내 주식 조회
            res = _kis_client.get_domestic_price(symbol)
            if res.get("rt_cd") != "0":
                raise HTTPException(status_code=400, detail=f"KIS API Error: {res.get('msg1')}")
            
            output = res.get("output", {})
            exchange = market or "KRX"
            
            result_data = {
                "symbol": symbol,
                "national": national,
                "exchange": exchange,
                "price": output.get("stck_prpr"),
                "change": output.get("prdy_vrss"),
                "change_rate": output.get("prdy_ctrt"),
                "volume": output.get("acml_vol"),
                "high": output.get("stck_hgpr"),
                "low": output.get("stck_lwpr"),
                "open": output.get("stck_oprc"),
                "timestamp": datetime.now().isoformat(),
                "raw_output": json.dumps(output) # Redis 저장을 위해 JSON 문자열로 변환
            }
            
            # Redis Key 생성
            if market:
                quote_key = meta.quote(national=national, exchange=market, symbol=symbol)

        else:
            # 해외 주식 조회
            if not market:
                raise HTTPException(status_code=400, detail="Market is required for overseas symbols")
            
            res = _kis_client.get_overseas_price_detail(market, symbol)
            if res.get("rt_cd") != "0":
                raise HTTPException(status_code=400, detail=f"KIS API Error: {res.get('msg1')}")
            
            output = res.get("output", {})
            
            result_data = {
                "symbol": symbol,
                "national": national,
                "exchange": market,
                "price": output.get("last"),
                "change": output.get("diff"),
                "change_rate": output.get("rate"),
                "volume": output.get("tvol"),
                "timestamp": datetime.now().isoformat(),
                "raw_output": json.dumps(output)
            }
            
            quote_key = meta.quote(national=national, exchange=market, symbol=symbol)

        # 2. Redis에 결과 저장 (TTL 설정)
        if _redis_client and quote_key:
            redis_key = quote_key.build()
            ttl_ms = quote_key.get_ttl() # ms 단위
            
            # Hash에 필드 저장
            # raw_output은 위에서 이미 json dumps 처리함
            save_data = {k: str(v) for k, v in result_data.items() if v is not None}
            
            await _redis_client.hset(redis_key, mapping=save_data)
            
            if ttl_ms:
                await _redis_client.pexpire(redis_key, ttl_ms)
                
            logger.info(f"Cached spot price for {symbol} to {redis_key} (TTL: {ttl_ms}ms)")

        # API 응답 시에는 raw_output을 다시 객체로 변환해서 줄 수도 있지만, 
        # 기존 컨벤션대로 딕셔너리로 반환 (JSON 응답)
        if "raw_output" in result_data and isinstance(result_data["raw_output"], str):
             result_data["raw_output"] = json.loads(result_data["raw_output"])

        return result_data

    except Exception as e:
        logger.exception(f"Failed to fetch spot price for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))
