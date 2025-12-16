# Ingestor 실행 모드 가이드

## 개요

`quote_pipeline`은 4가지 실행 모드 조합을 지원합니다:

| 모드 | Provider 수 | 심볼 관리 | 설명 |
|------|-------------|-----------|------|
| `single_static` | 1개 | 고정 | 가장 기본적인 형태 |
| `single_dynamic` | 1개 | Redis 동적 | 단일 provider + 동적 심볼 |
| `multi_static` | 여러 개 | 고정 | 여러 provider 동시 실행 |
| `multi_dynamic` | 여러 개 | Redis 동적 | 여러 provider + 동적 심볼 |

---

## 용어 정의

### Provider (single / multi)
- **single**: 단일 거래소/데이터 소스 (예: kis_new만)
- **multi**: 여러 거래소/데이터 소스 동시 실행 (예: kis_new + upbit + binance)

### Ingestor Mode (static / dynamic)
- **static**: 시작 시 설정된 심볼 고정, 변경 시 재시작 필요
- **dynamic**: Redis `active_symbols:{provider}` Set을 폴링하여 런타임 심볼 추가/제거

---

## 실행 예시

### 1. single_static (단일 provider, 고정 심볼)

```bash
PROVIDER=kis_new SYMBOLS=NVDA,AAPL,005930 \
REDIS_URL=redis://redis:6379/0 \
uv run python -m quote_pipeline.main
```

```
┌─────────────────────────────────────┐
│ kis_new ingestor                    │
│   symbols: [NVDA, AAPL, 005930]     │
│   (고정, 변경 시 재시작 필요)         │
└─────────────────────────────────────┘
```

### 2. single_dynamic (단일 provider, 동적 심볼)

```bash
PROVIDER=kis_new SYMBOLS=NVDA \
REDIS_URL=redis://redis:6379/0 \
uv run python -m quote_pipeline.main --dynamic
```

```
┌─────────────────────────────────────┐
│ kis_new ingestor                    │
│   폴링: active_symbols:kis_new      │
│   심볼 추가: redis-cli SADD ...     │
└─────────────────────────────────────┘
```

런타임에 심볼 추가/제거:
```bash
redis-cli SADD active_symbols:kis_new TSLA
redis-cli SREM active_symbols:kis_new NVDA
```

### 3. multi_static (다중 provider, 고정 심볼)

```bash
PROVIDERS=kis_new,upbit SYMBOLS=NVDA,005930,KRW-BTC \
uv run python -m quote_pipeline.main
```

```
┌─────────────────────────────────────┐
│ asyncio.gather                      │
│   ├── kis_new: [NVDA, 005930]       │ ← DB 조회로 자동 분류
│   └── upbit: [KRW-BTC]              │
└─────────────────────────────────────┘
```

### 4. multi_dynamic (다중 provider, 동적 심볼) - 권장

```bash
PROVIDERS=kis_new,upbit,binance SYMBOLS=NVDA,KRW-BTC,btcusdt \
REDIS_URL=redis://localhost:6379/0 \
uv run python -m quote_pipeline.main --dynamic
```

```
┌─────────────────────────────────────────────────────────┐
│ asyncio.gather                                          │
│   ├── kis_new: 폴링 active_symbols:kis_new             │
│   ├── upbit: 폴링 active_symbols:upbit                 │
│   └── binance: 폴링 active_symbols:binance             │
└─────────────────────────────────────────────────────────┘
```

---

## 심볼 자동 분류

`SYMBOLS` 환경변수에 여러 거래소의 심볼을 섞어서 입력해도 자동으로 provider별로 분류됩니다.

### 분류 로직 (`loaders/symbol_resolver.py`)

1. **패턴 매칭 (빠름)**
   - `KRW-*` → upbit
   - `*usdt`, `*btc` → binance

2. **DB 조회 (정확)**
   - `securities_master` 테이블에서 `national` 컬럼 확인
   - `KR`, `US`, `JP`, `CN`, `HK`, `VN` → kis_new

3. **기본값**
   - 매칭 안 되면 `kis_new`

### 예시

```python
symbols = ['NVDA', '005930', 'KRW-BTC', 'btcusdt']
# 결과:
# kis_new: {'NVDA', '005930'}  (DB에서 US/KR 확인)
# upbit: {'KRW-BTC'}           (패턴 매칭)
# binance: {'btcusdt'}         (패턴 매칭)
```

---

## Redis Set 구조 (Dynamic Mode)

```
active_symbols           # (사용 안 함, 레거시)
active_symbols:kis_new   # kis_new provider 전용
active_symbols:upbit     # upbit provider 전용
active_symbols:binance   # binance provider 전용
```

### Redis 명령어

```bash
# 현재 심볼 확인
redis-cli SMEMBERS active_symbols:kis_new

# 심볼 추가
redis-cli SADD active_symbols:kis_new TSLA

# 심볼 제거
redis-cli SREM active_symbols:kis_new NVDA

# 전체 심볼 확인 (모든 provider)
redis-cli SUNION active_symbols:kis_new active_symbols:upbit active_symbols:binance
```

---

## 코드 구조

```
quote_pipeline/
├── main.py                     # CLI 진입점
├── config.py                   # Settings, Provider enum
├── pipeline.py                 # build_ingestor, build_sink
├── ingestors/
│   ├── manage_ingestor.py      # 4가지 모드 함수
│   │   ├── run_single_static()
│   │   ├── run_single_dynamic()
│   │   ├── run_multi_static()
│   │   ├── run_multi_dynamic()
│   │   └── run_ingestor()      # 통합 진입점
│   ├── active_symbols_store.py # Redis Set 유틸
│   ├── kis_new.py              # KIS 인게스터
│   ├── upbit.py                # Upbit 인게스터
│   └── binance.py              # Binance 인게스터
└── loaders/
    └── symbol_resolver.py      # 심볼 → provider 분류
```

---

## 환경변수 정리

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `PROVIDER` | 단일 provider | `kis_new` |
| `PROVIDERS` | 다중 provider (콤마 구분) | `kis_new,upbit,binance` |
| `SYMBOLS` | 심볼 목록 (콤마 구분) | `NVDA,KRW-BTC,btcusdt` |
| `DYNAMIC_ENABLED` | 동적 모드 활성화 | `true` |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379/0` |
| `ACTIVE_SYMBOL_SET` | Redis Set 베이스 이름 | `active_symbols` |
| `ACTIVE_SYMBOL_POLL_INTERVAL` | 폴링 주기 (초) | `5` |

---

## 모드 선택 가이드

| 상황 | 권장 모드 |
|------|-----------|
| 개발/테스트 | `single_static` |
| 단일 거래소, 심볼 자주 변경 | `single_dynamic` |
| 여러 거래소, 심볼 고정 | `multi_static` |
| 프로덕션 (여러 거래소, 동적 관리) | `multi_dynamic` |
