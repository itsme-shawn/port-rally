"""
KIS 순수 REST 호출 진입점:
- access_token 발급/캐싱 (kis_auth)
- 국내/해외 현재가 조회 (kis_rest)
"""

import argparse
import logging
import os

from dotenv import load_dotenv

from quote_pipeline.ingestors.kis_pure import KisConfig, KisRestAuthClient, KisRestClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KIS REST 기본 테스트 (access_token 캐싱 포함)")
    sub = parser.add_subparsers(dest="command", required=True)

    over = sub.add_parser("overseas", help="해외주식 현재가 조회")
    over.add_argument("--excd", required=True, help="거래소 코드 (예: NAS/BAQ 등)")
    over.add_argument("--symbol", required=True, help="종목코드 (예: AAPL)")

    dom = sub.add_parser("domestic", help="국내주식 현재가 체결 조회")
    dom.add_argument("--symbol", required=True, help="단축코드 6자리 (예: 005930)")
    dom.add_argument("--market", default="J", help="FID_COND_MRKT_DIV_CODE 기본 J(KRX)")

    parser.add_argument("--log-level", default="INFO", help="INFO/DEBUG")
    parser.add_argument("--vts", action="store_true", help="모의투자 도메인 사용")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    appkey = os.getenv("KIS_APP_KEY")
    appsecret = os.getenv("KIS_APP_SECRET")
    if not appkey or not appsecret:
        raise RuntimeError("환경변수 KIS_APP_KEY, KIS_APP_SECRET 이 필요합니다.")

    cfg = KisConfig(app_key=appkey, app_secret=appsecret, is_vts=args.vts)
    auth = KisRestAuthClient(cfg)
    rest = KisRestClient(cfg, auth)

    if args.command == "overseas":
        data = rest.get_overseas_price_detail(args.excd, args.symbol)
        logging.info("Overseas price (%s/%s): %s", args.excd, args.symbol, data)
        return

    if args.command == "domestic":
        data = rest.get_domestic_price(args.symbol, market_div=args.market)
        logging.info("Domestic price (%s): %s", args.symbol, data)
        return


if __name__ == "__main__":
    main()
