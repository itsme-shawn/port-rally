import logging
import os
import sys
import argparse
from pathlib import Path

# 0. PYTHONPATH 자동 설정 (src 디렉토리 추가)
# 현재 파일 위치: services/market-data/tests/manual/test_kis_rest.py
# 목표 src 위치: services/market-data/src
current_dir = Path(__file__).resolve().parent
market_data_root = current_dir.parent.parent
src_path = market_data_root / "src"
sys.path.append(str(src_path))

from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from quote_pipeline.clients.kis.kis_config import KisConfig
from quote_pipeline.clients.kis.kis_auth_client import KisRestAuthClient
from quote_pipeline.clients.kis.kis_rest_client import KisRestClient

def test_kis_rest_spot_price(symbol: str):
    # .env 로드 순서:
    # 1. services/market-data/.env (우선순위 높음)
    # 2. 프로젝트 루트 .env (공통 설정)
    
    project_root = market_data_root.parent.parent # /workspaces/port-rally
    
    # 루트 .env 로드
    root_env = project_root / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env)
        
    # market-data .env 로드 (override)
    service_env = market_data_root / ".env"
    if service_env.exists():
        load_dotenv(dotenv_path=service_env, override=True)
    
    # 환경 변수 확인 (KIS_APP_KEY, KIS_APP_SECRET)
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    
    if not all([app_key, app_secret]):
        logger.error("Missing KIS environment variables (KIS_APP_KEY, KIS_APP_SECRET).")
        return

    # 1. Config 및 Auth Client 초기화
    # 실전투자(is_vts=False) 기준
    config = KisConfig(app_key=app_key, app_secret=app_secret, is_vts=False)
    auth_client = KisRestAuthClient(config)
    
    # 2. REST Client 초기화
    rest_client = KisRestClient(config, auth_client)
    
    # 3. 주식 현재가 조회
    logger.info(f"Fetching domestic spot price for {symbol}...")
    
    try:
        response = rest_client.get_domestic_price(symbol)
        output = response.get("output", {})
        
        if response.get("rt_cd") == "0":
            logger.info("Successfully fetched data!")
            
            print(f"\n[Spot Price Info for {symbol}]")
            print(f"Current Price: {output.get('stck_prpr')}")
            print(f"Change: {output.get('prdy_vrss')} ({output.get('prdy_ctrt')}%) ")
            print(f"Volume: {output.get('acml_vol')}")
            print(f"Open: {output.get('stck_oprc')}")
            print(f"High: {output.get('stck_hgpr')}")
            print(f"Low: {output.get('stck_lwpr')}")
            print("-" * 30)
        else:
            logger.error(f"Error from KIS API: {response.get('msg1')}")
            
    except Exception as e:
        logger.exception(f"An error occurred while calling KIS API: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KIS Spot Price Test")
    parser.add_argument("--symbol", type=str, default="005930", help="Stock symbol (e.g., 005930)")
    args = parser.parse_args()
    
    test_kis_rest_spot_price(args.symbol)
