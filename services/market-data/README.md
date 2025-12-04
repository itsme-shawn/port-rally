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
uv venv --python 3.12 # 현재 디렉토리 기준으로 .venv/ vhfej todtjd
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
```

## 환경 변수 (옵션)
- `LOG_LEVEL`: 기본 `INFO`, `DEBUG` 시 상세 패킷 로그.
- `REDIS_URL`: 설정 시 Redis Sink 사용(`redis://localhost:6379/0` 형식). 미설정 시 stdout Sink.

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
