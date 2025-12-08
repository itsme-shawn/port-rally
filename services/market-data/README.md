# Market Data Service (Phase 0)

Phase 0 목표: **실시간 시세 WebSocket 연결 안정성 PoC**와 간단한 로깅/분배 파이프라인 골격을 만든다. (Redis 등 외부 인프라는 선택적으로 연결)

## 기능 개요
- Upbit/Binance WebSocket 구독 예제
- 재연결(backoff) + 헬스 로깅
- 싱크(Sink) 인터페이스: 기본은 `stdout`, 확장 시 Redis 등으로 교체

## 빠른 시작 (uv, Python 3.12 권장)
```bash

curl -LsSf https://astral.sh/uv/install.sh | sh        # uv 미설치 시

# (1) Python 3.12 설치 (pyenv 역할)
uv python install 3.12
# (2) Python 3.12를 사용해 가상환경 생성 (venv 역할)
cd services/market-data
uv venv --python 3.12              # 현재 디렉토리 기준으로 .venv/ 생성
# (3) 가상환경 활성화
source .venv/bin/activate
# (4) 패키지 설치 또는 동기화
uv sync            # pyproject.toml + uv.lock 기준으로 설치
# (5) python 모듈 검색 경로 지정
export PYTHONPATH=src

# 예) 업비트 KRW-BTC/KRW-ETH 시세 스트림
uv run -m quote_pipeline.main --provider upbit --symbols KRW-BTC,KRW-ETH

# 예) 바이낸스 BTCUSDT/ETHUSDT 트레이드 스트림
uv run -m quote_pipeline.main --provider binance --symbols btcusdt,ethusdt --channel trade

# 예) KIS NVDA 체결 스트림 (env로 자격 설정 필요)
# env: KIS_ID, KIS_ACCOUNT, KIS_APP_KEY, KIS_APP_SECRET
uv run -m quote_pipeline.main --provider kis --symbols NVDA
 
# Redis 없이 stdout만 쓰려면 REDIS_URL을 비우거나 null/none/stdout로 설정
# --rm 옵션 : 일회성 실행 후 컨테이너 삭제
docker compose run --rm --build -e REDIS_URL=stdout -e PROVIDER=upbit -e SYMBOLS=KRW-BTC market-data
```

## 환경 변수 (옵션)
- `LOG_LEVEL`: 기본 `INFO`, `DEBUG` 시 상세 패킷 로그.
- `REDIS_URL`: 설정 시 Redis Sink 사용(`redis://localhost:6379/0` 형식). 미설정 시 stdout Sink.

## KIS 실시간 수신 테스트 (NVDA, 005930 등)
테스트용 단독 스크립트 위치: `src/kis_test/kis_realtime.py`
```bash
cd services/market-data
uv sync
source .venv/bin/activate
export PYTHONPATH=src

# 간단 테스트: NASDAQ NVDA 체결가 구독 → stdout
# Redis 정보는 .env로 관리 (옵션)
uv run -m kis_test.kis_realtime --symbol NVDA

# Redis Pub/Sub 발행
uv run -m kis_test.kis_realtime \
  --env REDIS_URL=redis://localhost:6379/0 \
  --env REDIS_CHANNEL=kis-quotes
```
환경:
- `KIS_ID`, `KIS_ACCOUNT`, `KIS_APP_KEY`, `KIS_APP_SECRET` (env 필수)
- Redis를 쓰지 않으면 stdout으로만 출력됨. Redis를 쓰려면 `REDIS_URL`, `REDIS_CHANNEL`을 env로 설정.

## 구조
```
services/market-data/
├── pyproject.toml
├── README.md
└── src/quote_pipeline
    ├── main.py           # CLI 엔트리
    ├── config.py         # 설정/파라미터
    ├── logging_config.py # 로깅 설정
    ├── pipeline.py       # Ingestor + Sink 조립
    ├── ingestors/        # 거래소별 WebSocket 인게스터
    └── sinks/            # Sink 인터페이스 (stdout, redis 등)
```

## Phase 0 검증 체크리스트
- WebSocket 연결 확인
- Redis 연결 시 Pub/Sub 발행 정상 여부 확인

## 테스트 아키텍처 (초안)
- 러너/도구: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`/`unittest.mock`.
- 디렉토리 제안:
  ```
  services/market-data/tests/
    conftest.py            # 공용 fixture (event loop, redis mock 등)
    test_trading_hours.py  # 장시간/시장 판정 유틸
    test_stdout_sink.py    # stdout sink 직렬화/출력 검증
    test_pipeline.py       # provider별 ingestor/sink 선택 검증
    fixtures/              # 샘플 메시지, fake 서버 핸들러(필요 시)
  ```
- 대상:
  - Utils: `is_market_open`, `infer_market_from_symbol` 등 순수 함수
  - Sinks: Redis는 `fakeredis`/mock publish, stdout는 `capsys` 캡처
  - Ingestors: fake websocket/pykis로 메시지 1건 발행 → sink 호출 검증, Decimal/datetime 직렬화 확인
  - Pipeline: 설정에 따른 ingestor/sink 선택, channel override 반영
- 실행 예:
  ```
  cd services/market-data
  uv run -m pytest tests
  (pyproject.toml 에 tests 경로 세팅해놔서 `uv run -m pytest` 로도 테스트 수행됨)
  ```
- 커버리지:
  ```
  cd services/market-data
  uv run -m pytest --cov=quote_pipeline --cov-report=term-missing
  ```
- 통합 테스트는 필요 시 `tests/integration/`에서 실제 Redis를 사용한 스모크로 분리
