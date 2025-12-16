# KIS Pure 흐름 요약 (함수 단위)

## 진입점: `services/market-data/src/quote_pipeline/ingestors/kis_pure/kis_main.py`
- **`main()`**
  - `.env` 로드 후 CLI 인자 파싱.
  - `KisConfig` 생성(모의투자 여부 `--vts` 반영).
  - REST 인증/조회: `KisRestAuthClient` → `KisRestClient`로 해외(`overseas`)·국내(`domestic`) 현재가 조회.
  - WS 테스트: `KisWsAuthClient`로 승인키 캐시/발급 후 `KisWsClient.stream_once` 호출.

- **`parse_args()`**
  - `overseas`(EXCD, 심볼), `domestic`(심볼, 시장코드), `ws`(심볼, TR ID, 옵션 ws-url) 서브커맨드 정의.
  - 공통 옵션: `--log-level`, `--vts`.

## 인증: `kis_auth.py`
- **`KisRestAuthClient`**
  - `/oauth2/tokenP` 접근토큰 발급 + 파일 캐시(`token_cache_rest.json`).
  - `get_valid_access_token(buffer_sec=60)`: 캐시가 유효하면 재사용, 만료 임박 시 재발급 후 저장.
  - 만료 시각은 `access_token_token_expired`(파싱 실패 시 `expires_in`) 기반.

- **`KisWsAuthClient`**
  - `/oauth2/Approval` 승인키 발급 + 파일 캐시(`token_cache_ws.json`).
  - `get_valid_approval_key(buffer_sec=60)`: 캐시가 유효하면 재사용, 만료 임박 시 재발급 후 저장.
  - 기본 유효기간은 24시간(`validity_seconds`).

## REST 조회: `kis_rest.py`
- **`KisRestClient`**
  - `KisRestAuthClient`의 `get_valid_access_token()`으로 토큰 확보 → 공통 헤더 생성.
  - `get_domestic_price(code, market_div="J")`: FHKST01010300 현재가 체결(국내).
  - `get_overseas_price_detail(excd, symbol, auth="")`: HHDFS00000300 해외 현재체결가.

## WebSocket (단순 테스트): `kis_ws.py`
- **`KisWsClient`**
  - 승인키는 내부 `issue_approval_key()` (캐시 없음)으로 발급.
  - `_build_ws_message(tr_id, tr_key, tr_type="1")`: 등록/해제 메시지 생성.
  - `stream_once(symbol, tr_id, ws_url=None)`: 단일 심볼 구독 테스트, 수신 메시지를 로그 출력.
  - `subscribe_domestic_ticks(symbols)`, `subscribe_overseas_askbid(items)`: 다중 구독용 기본 구현(현재 수신만 출력).

## 설정/파이프라인
- `config.py`: Provider(현재 upbit/binance/kis), Redis/동적 구독 설정 등. `KisRestAuthClient`/`KisWsAuthClient`는 kis_pure 흐름에서 직접 사용.
- `pipeline.py`: 기존 Upbit/Binance/Kis 인게스터용. `kis_pure` 흐름은 별도(`kis_main.py` 실행)로 동작.

## 실행 예
- REST 해외: `uv run -m quote_pipeline.ingestors.kis_pure.kis_main overseas --excd NAS --symbol AAPL`
- REST 국내: `uv run -m quote_pipeline.ingestors.kis_pure.kis_main domestic --symbol 005930`
- WS 테스트: `uv run -m quote_pipeline.ingestors.kis_pure.kis_main ws --symbol AAPL --tr-id HDFSCNT0`

필수 환경변수: `KIS_APP_KEY`, `KIS_APP_SECRET` (옵션: `--vts`로 모의투자 도메인) 
