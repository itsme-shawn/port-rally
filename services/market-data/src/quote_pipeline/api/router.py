import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from quote_pipeline.clients.kis.kis_config import KisConfig
from quote_pipeline.clients.kis.kis_auth_client import KisRestAuthClient
from quote_pipeline.clients.kis.kis_rest_client import KisRestClient
from quote_pipeline.config import Settings
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/quotes")

# 전역 클라이언트 (서버 시작 시 초기화 권장)
_kis_client: Optional[KisRestClient] = None

def init_api_clients(settings: Settings):
    global _kis_client
    # KIS REST 클라이언트 초기화
    config = KisConfig(
        app_key=settings.kis.appkey,
        app_secret=settings.kis.secretkey,
        is_vts=False  # 실전투자 기준
    )
    auth = KisRestAuthClient(config)
    _kis_client = KisRestClient(config, auth)
    logger.info("API Clients (KIS REST) initialized")

@router.get("/spot")
async def get_spot_price(
    symbol: str = Query(..., description="종목 코드 (예: 005930)"),
    national: str = Query("KR", description="국가 코드 (KR, US 등)"),
    market: Optional[str] = Query(None, description="거래소 코드 (KOSPI, KOSDAQ, NAS 등)")
):
    """
    특정 종목의 현재가(Spot Price)를 KIS REST API를 통해 즉시 조회합니다.
    """
    if not _kis_client:
        raise HTTPException(status_code=503, detail="KIS client not initialized")

    try:
        if national == "KR":
            # 국내 주식 조회
            res = _kis_client.get_domestic_price(symbol)
            if res.get("rt_cd") != "0":
                raise HTTPException(status_code=400, detail=f"KIS API Error: {res.get('msg1')}")
            
            output = res.get("output", {})
            return {
                "symbol": symbol,
                "national": national,
                "exchange": market or "KRX",
                "price": output.get("stck_prpr"),
                "change": output.get("prdy_vrss"),
                "change_rate": output.get("prdy_ctrt"),
                "volume": output.get("acml_vol"),
                "high": output.get("stck_hgpr"),
                "low": output.get("stck_lwpr"),
                "open": output.get("stck_oprc"),
                "raw_output": output # 디버깅용 전체 데이터
            }
        else:
            # 해외 주식 조회 (현재는 국내 주식 위주로 구현, 필요 시 확장)
            if not market:
                raise HTTPException(status_code=400, detail="Market is required for overseas symbols")
            
            res = _kis_client.get_overseas_price_detail(market, symbol)
            if res.get("rt_cd") != "0":
                raise HTTPException(status_code=400, detail=f"KIS API Error: {res.get('msg1')}")
            
            output = res.get("output", {})
            return {
                "symbol": symbol,
                "national": national,
                "exchange": market,
                "price": output.get("last"),
                "change": output.get("diff"),
                "change_rate": output.get("rate"),
                "volume": output.get("tvol"),
                "raw_output": output
            }

    except Exception as e:
        logger.exception(f"Failed to fetch spot price for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))
