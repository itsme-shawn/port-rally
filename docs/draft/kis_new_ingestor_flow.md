# KIS New Ingestor 흐름 분석

## 개요

`kis_new` 인게스터는 한국투자증권(KIS) OpenAPI를 직접 사용하여 국내/해외 주식 실시간 시세를 수신하는 모듈입니다.
기존 `pykis` 라이브러리 기반의 `kis` 인게스터와 달리, WebSocket API를 직접 호출합니다.

---

## 1. 전체 실행 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              main.py                                        │
│                                                                             │
│  1. parse_args() → CLI 인자 파싱                                            │
│  2. build_settings_from_args(args) → Settings 객체 생성                     │
│  3. build_sink(settings) → Sink 생성 (Redis or Stdout)                      │
│  4. dynamic.enabled 여부에 따라 분기                                         │
│                                                                             │
│     ┌─────────────────────────┐    ┌─────────────────────────────────────┐  │
│     │ dynamic=False (정적)    │    │ dynamic=True (동적)                 │  │
│     │                         │    │                                     │  │
│     │ build_ingestor()        │    │ manage_dynamic_ingestor()           │  │
│     │ ingestor.run_forever()  │    │ → Redis active_symbols 폴링         │  │
│     └─────────────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 설정 흐름 (config.py)

### 2.1 환경변수 → Settings 객체

```python
# 환경변수
PROVIDER=kis_new
SYMBOLS=NVDA,AAPL,005930
DYNAMIC_ENABLED=true
ACTIVE_SYMBOL_SET=active_symbols
ACTIVE_SYMBOL_POLL_INTERVAL=5
REDIS_URL=redis://localhost:6379/0
KIS_APP_KEY=...
KIS_APP_SECRET=...
```

### 2.2 주요 Config 클래스

| 클래스 | 역할 |
|--------|------|
| `Provider` | 거래소 enum (`upbit`, `binance`, `kis`, `kis_new`) |
| `KisConfig` | KIS API 인증 정보 (`appkey`, `secretkey`) |
| `DynamicConfig` | 동적 구독 설정 (`enabled`, `active_set`, `poll_interval_s`) |
| `Settings` | 전체 설정 통합 |

---

## 3. Ingestor 생성 (pipeline.py)

### 3.1 build_ingestor() 함수

```python
def build_ingestor(settings: Settings, sink: Sink):
    if settings.provider == Provider.kis_new:
        return KisNewIngestor(
            symbols=settings.symbols,
            sink=sink,
            appkey=settings.kis.appkey,
            appsecret=settings.kis.secretkey,
            reconnect_base_delay=settings.common.reconnect_base_delay,
            reconnect_max_delay=settings.common.reconnect_max_delay,
        )
```

### 3.2 KisNewIngestor 초기화

```
KisNewIngestor
├── symbols: Set[str]          # 구독할 심볼 집합
├── sink: Sink                 # 출력 대상 (Redis/Stdout)
├── ws_client: KisWsClient     # WS 메시지 빌더
└── sessions: Dict[str, _TrSession]  # TR_ID별 세션
    ├── "H0UNCNT0" → 국내 체결가 세션
    └── "HDFSCNT0" → 해외 체결가 세션
```

---

## 4. Active Symbols 동적 구독 (active_symbols.py)

### 4.1 동작 원리

```
┌─────────────────────────────────────────────────────────────────────┐
│                    manage_dynamic_ingestor()                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. Redis 연결                                                │   │
│  │    redis_client = redis.from_url(settings.redis.url)        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 2. 초기 심볼 seed (환경변수 SYMBOLS)                         │   │
│  │    redis_client.sadd("active_symbols", *settings.symbols)   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 3. 초기 심볼로 ingestor 시작                                 │   │
│  │    current_symbols = fetch_active_symbols()                 │   │
│  │    task, ingestor = start_ingestor(current_symbols)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 4. 폴링 루프 (매 5초)                                        │   │
│  │    while True:                                               │   │
│  │        sleep(poll_interval_s)                               │   │
│  │        new_symbols = fetch_active_symbols()                 │   │
│  │        if new_symbols != current_symbols:                   │   │
│  │            ingestor.apply_symbols(new_symbols)  ← 핵심!     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 fetch_active_symbols()

```python
async def fetch_active_symbols(redis_client, set_name: str) -> Set[str]:
    raw = await redis_client.smembers(set_name)  # Redis SMEMBERS 명령
    return set(raw or [])
```

- Redis Set `active_symbols`에서 현재 구독 중인 심볼 목록을 가져옴
- 반환값: `{"NVDA", "AAPL", "005930"}`

### 4.3 심볼 변경 감지 및 적용

```python
if new_symbols != current_symbols:
    logger.info("Active symbols changed: %s -> %s", current_symbols, new_symbols)
    current_symbols = new_symbols

    # kis_new는 apply_symbols 메서드를 제공
    if ingestor and hasattr(ingestor, "apply_symbols"):
        await ingestor.apply_symbols(current_symbols)
    # upbit/binance는 재시작
    else:
        task.cancel()
        task, ingestor = await start_ingestor(current_symbols)
```

**핵심 차이점:**
- `kis_new`: `apply_symbols()` 호출 → WS 연결 유지하면서 구독만 변경
- `upbit/binance`: ingestor 재시작 → WS 재연결

---

## 5. KisNewIngestor 상세 (kis_new.py)

### 5.1 클래스 구조

```
KisNewIngestor
│
├── apply_symbols(symbols)     # 외부에서 호출되는 메서드
│   └── 심볼을 시장별로 분류 후 _TrSession에 전달
│
├── run_forever()              # 메인 루프 (단순 keepalive)
│
└── sessions: Dict[str, _TrSession]
    │
    ├── _TrSession("H0UNCNT0")  # 국내 체결가
    │   ├── desired: Set[str]   # 원하는 심볼
    │   ├── current: Set[str]   # 현재 구독 중인 심볼
    │   ├── ws: WebSocket       # WS 연결
    │   └── task: asyncio.Task  # 백그라운드 태스크
    │
    └── _TrSession("HDFSCNT0")  # 해외 체결가
        └── (동일 구조)
```

### 5.2 apply_symbols() 흐름

```python
async def apply_symbols(self, symbols: Iterable[str]) -> None:
    """전체 심볼을 시장별로 분리해 TR_ID 세션에 전달."""
    self.desired_symbols = set(symbols)

    # 시장별 분류
    tr_map = {"H0UNCNT0": set(), "HDFSCNT0": set()}
    for sym in self.desired_symbols:
        market = infer_market_from_symbol(sym)  # "KR" or "US"
        if market == "KR":
            tr_map["H0UNCNT0"].add(sym)   # 국내
        else:
            tr_map["HDFSCNT0"].add(sym)   # 해외

    # 각 세션에 심볼 적용
    for tr_id, sym_set in tr_map.items():
        session = self.sessions.get(tr_id)
        if sym_set:
            if not session:
                session = _TrSession(tr_id, ...)
                session.start()  # 백그라운드 태스크 시작
            await session.apply_symbols(sym_set)
```

### 5.3 _TrSession.apply_symbols() - 증분 구독

```python
async def apply_symbols(self, symbols: Set[str]) -> None:
    self.desired = set(symbols)

    if not self.ws:
        # WS 미연결 시 pending
        return

    # 증분 계산
    to_add = self.desired - self.current      # 새로 추가할 심볼
    to_remove = self.current - self.desired   # 제거할 심볼

    # 구독 해제
    for sym in to_remove:
        await self._unregister(sym)

    # 구독 등록
    for sym in to_add:
        await self._register(sym)

    self.current = set(self.desired)
```

### 5.4 WS 구독 메시지

```python
async def _register(self, sym: str) -> None:
    tr_key = self._tr_key(sym)  # "005930" or "DNASNVDA"
    req = self.ws_client._build_ws_message(self.tr_id, tr_key, tr_type="1")  # 구독
    await self.ws.send(req)

async def _unregister(self, sym: str) -> None:
    req = self.ws_client._build_ws_message(self.tr_id, tr_key, tr_type="2")  # 해지
    await self.ws.send(req)
```

---

## 6. 시퀀스 다이어그램

```
┌──────┐     ┌──────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────┐
│Client│     │  Redis   │     │active_symbols│     │KisNewIngestor│     │KIS WS│
└──┬───┘     └────┬─────┘     └──────┬──────┘     └──────┬──────┘     └──┬──┘
   │              │                  │                   │               │
   │ SADD active_symbols TSLA       │                   │               │
   │─────────────>│                  │                   │               │
   │              │                  │                   │               │
   │              │    poll (5초)    │                   │               │
   │              │<─────────────────│                   │               │
   │              │                  │                   │               │
   │              │  SMEMBERS        │                   │               │
   │              │<─────────────────│                   │               │
   │              │                  │                   │               │
   │              │ {NVDA,AAPL,TSLA} │                   │               │
   │              │─────────────────>│                   │               │
   │              │                  │                   │               │
   │              │                  │ apply_symbols()   │               │
   │              │                  │──────────────────>│               │
   │              │                  │                   │               │
   │              │                  │                   │ subscribe TSLA│
   │              │                  │                   │──────────────>│
   │              │                  │                   │               │
   │              │                  │                   │  price data   │
   │              │                  │                   │<──────────────│
   │              │                  │                   │               │
   │              │     PUBLISH      │                   │               │
   │              │<─────────────────────────────────────│               │
   │              │                  │                   │               │
```

---

## 7. 데이터 흐름 요약

```
1. 환경변수/CLI → Settings 객체
2. Settings → Sink 생성 (Redis/Stdout)
3. Settings → KisNewIngestor 생성
4. Redis Set "active_symbols" ← 초기 심볼 seed

5. [폴링 루프]
   Redis SMEMBERS "active_symbols"
   → 심볼 변경 감지
   → KisNewIngestor.apply_symbols(new_symbols)
   → _TrSession.apply_symbols(시장별 심볼)
   → 증분 구독/해지 (register/unregister)

6. [메시지 수신]
   KIS WS → _handle_message() → sink.publish()
```

---

## 8. Redis 명령어 참고

```bash
# 현재 구독 중인 심볼 확인
redis-cli SMEMBERS active_symbols

# 심볼 추가
redis-cli SADD active_symbols TSLA

# 심볼 제거
redis-cli SREM active_symbols NVDA

# 전체 초기화
redis-cli DEL active_symbols
```

---

## 9. 환경변수 정리

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `PROVIDER` | 거래소 선택 | (필수) |
| `SYMBOLS` | 초기 심볼 (쉼표 구분) | (빈 문자열) |
| `DYNAMIC_ENABLED` | 동적 구독 활성화 | `false` |
| `ACTIVE_SYMBOL_SET` | Redis Set 이름 | `active_symbols` |
| `ACTIVE_SYMBOL_POLL_INTERVAL` | 폴링 주기(초) | `5` |
| `REDIS_URL` | Redis 연결 URL | (필수 for dynamic) |
| `KIS_APP_KEY` | KIS API App Key | (필수) |
| `KIS_APP_SECRET` | KIS API App Secret | (필수) |

---

## 10. 실행 예시

```bash
# 정적 모드 (심볼 고정)
PROVIDER=kis_new SYMBOLS=NVDA,AAPL KIS_APP_KEY=... KIS_APP_SECRET=... \
uv run python -m quote_pipeline.main

# 동적 모드 (Redis active_symbols 폴링)
PROVIDER=kis_new SYMBOLS=NVDA,AAPL \
DYNAMIC_ENABLED=true REDIS_URL=redis://localhost:6379/0 \
KIS_APP_KEY=... KIS_APP_SECRET=... \
uv run python -m quote_pipeline.main --dynamic
```
