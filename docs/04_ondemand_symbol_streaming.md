# 온디맨드 시세 스트리밍 시스템

> **최종 수정일**: 2026-01-05
> **관련 서비스**: services/market-data, apps/core-api
> **관련 문서**: [Market Data Pipeline](./03_marketdata_pipeline.md), [DB Schema](./db_schema.md)

---

## 목차

1. [왜 온디맨드 방식인가?](#1-왜-온디맨드-방식인가)
2. [핵심 개념](#2-핵심-개념)
3. [Active Symbols 시스템](#3-active-symbols-시스템)
4. [동작 원리](#4-동작-원리)
5. [사용자 시나리오](#5-사용자-시나리오)
6. [Provider별 구독 전략](#6-provider별-구독-전략)
7. [운영 가이드](#7-운영-가이드)
8. [아키텍처 히스토리](#8-아키텍처-히스토리)

---

## 1. 왜 온디맨드 방식인가?

### 1.1 문제 정의

소규모 시스템에서 WebSocket 으로 전체 종목 시세를 실시간으로 뿌려주고자 할 때 다음과 같은 문제를 가진다:

**전체 구독 방식의 문제점**:
```
전체 종목 구독 (예: KOSPI 900개 + KOSDAQ 1,500개 + 해외 주식 수천 개)
  ↓
- 불필요한 네트워크 트래픽 (99% 이상이 사용되지 않는 데이터)
- Redis 메모리 낭비 (모든 종목의 시세를 캐싱)
- WebSocket 연결 부하 (API 제한 초과 위험)
- 인프라 비용 증가
```

### 1.2 온디맨드 방식의 해결책

**핵심 아이디어**: "사용자가 관심 있는 종목만 실시간으로 구독한다"

```
사용자 행동 → active_symbols 추가 → 실시간 구독 시작
   ↓
검색/관심종목/포트폴리오 → Redis Set 관리 → WebSocket 구독 활성화
   ↓
결과: 최소한의 리소스로 최적의 UX 제공
```

**효과**:
- ✅ **비용 절감**: 전체 종목의 1-5%만 구독 (95% 이상 절감)
- ✅ **Cold Start 해결**: 최초 REST 조회 후 WebSocket 전환으로 즉시 실시간 시세 제공
- ✅ **UX 향상**: 사용자 관심 종목은 항상 최신 시세 유지
- ✅ **확장성**: 사용자 증가에도 선형적 확장 가능

---

## 2. 핵심 개념

### 2.1 온디맨드 구독 원칙

```
전체 종목 (수만 개)
    ↓
사용자 관심 종목만 선택적 구독 (수십~수백 개)
    ↓
TTL 기반 자동 정리 (검색 종목은 5-10분 후 제거)
    ↓
영구 구독 (관심종목/포트폴리오는 계속 유지)
```

### 2.2 Provider별 독립 관리

각 거래소는 독립적인 구독 Set을 가진다:

```
active_symbols:kis_new    # KIS (국내/해외 주식)
active_symbols:upbit      # Upbit (가상화폐)
active_symbols:binance    # Binance (가상화폐)
```

**격리의 장점**:
1. **API 특성 반영**: KIS는 증분 구독, Upbit는 재구독 방식으로 각각 최적화
2. **독립적 장애 처리**: 한 Provider의 문제가 다른 Provider에 영향 없음
3. **심볼 충돌 방지**: 같은 심볼이 다른 Provider에 존재해도 독립적으로 관리

### 2.3 TTL 기반 구독 관리

| 구독 유형 | TTL | 설명 |
|----------|-----|------|
| **검색 종목** | 5-10분 | 검색 직후 시세 변동을 실시간으로 보여주기 위함 |
| **관심종목** | 영구 | 사용자가 명시적으로 추가한 종목 |
| **포트폴리오** | 영구 | 보유 종목은 항상 실시간 시세 제공 |
| **인기종목** | 1시간 | (선택적) 시스템 전체의 인기 종목 |

---

## 3. Active Symbols 시스템

### 3.1 Redis Set 구조

```
Redis
├── active_symbols:kis_new
│   ├── "005930" (삼성전자)
│   ├── "000660" (SK하이닉스)
│   ├── "NVDA" (엔비디아)
│   └── "TSLA" (테슬라)
│
├── active_symbols:upbit
│   ├── "KRW-BTC"
│   └── "KRW-ETH"
│
└── active_symbols:binance
    ├── "btcusdt"
    └── "ethusdt"
```

### 3.2 동적 구독 흐름

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│ 사용자/API   │─(1)─▶│  Redis Set   │◀─(2)─│ IngestorManager│
│             │      │ active_      │      │ (5초 폴링)     │
│ SADD/SREM   │      │ symbols:*    │      └────────┬───────┘
└─────────────┘      └──────────────┘               │
                                                    (3)
                                                     ▼
                                      ┌─────────────────────────┐
                                      │ KisClient.apply_symbols()│
                                      │ (증분 구독)              │
                                      └────────┬────────────────┘
                                               │
                                              (4)
                                               ▼
                                      ┌─────────────────────────┐
                                      │ WebSocket 구독          │
                                      │ REGISTER/UNREGISTER     │
                                      └─────────────────────────┘
```

**(1) 사용자/API**: Redis에 심볼 추가/제거
**(2) 폴링**: 5초마다 Redis Set 변경 감지
**(3) 증분 계산**: 추가/제거할 심볼만 추출
**(4) WebSocket 구독**: 변경된 심볼만 구독/해지

### 3.3 증분 구독 지원 현황

| Provider | 증분 구독 | 변경 시 동작 | WebSocket 연결 |
|----------|----------|-------------|---------------|
| **KIS** | ✅ 개별 증분 | 변경된 심볼만 등록/해지 메시지 전송 | 유지 |
| **Upbit** | ✅ 전체 재구독 | 전체 심볼 목록 재전송 | 유지 |
| **Binance** | ❌ 미구현 | Ingestor 재시작 (재연결) | 재연결 |

**증분 구독의 장점**:
- WebSocket 연결 유지 (재연결 오버헤드 없음)
- 무중단 심볼 변경 (시세 수신 중단 없음)
- 최소한의 메시지만 전송 (네트워크 효율)

---

## 4. 동작 원리

### 4.1 전체 아키텍처

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 거래소 API    │────▶│ Market Data  │────▶│    Redis     │
│ (WebSocket)  │     │   Service    │     │              │
└──────────────┘     └──────────────┘     │ - quote:*    │
                                           │ - active_    │
                                           │   symbols:*  │
                                           └──────┬───────┘
                                                  │
                        ┌─────────────────────────┼─────────────────────────┐
                        ▼                         ▼                         ▼
                   ┌─────────┐            ┌─────────────┐         ┌─────────────┐
                   │Core API │            │Quote Cache  │         │WS Gateway   │
                   │(REST)   │            │Updater      │         │(클라이언트   │
                   └─────────┘            │(Redis       │         │WebSocket)   │
                                          │ pub/sub)    │         └─────────────┘
                                          └─────────────┘
```

### 4.2 폴링 루프 (IngestorManager)

**파일**: [ingestor_manager.py:147-220](../services/market-data/src/quote_pipeline/ingestors/ingestor_manager.py#L147-L220)

```python
async def _run_dynamic_symbol_loop(provider: Provider):
    """
    Redis Set 폴링 및 심볼 변경 감지

    주기: 5초 (환경변수 ACTIVE_SYMBOL_POLL_INTERVAL로 조정 가능)
    """
    current_symbols = await _get_symbols_from_redis(provider)

    while True:
        await asyncio.sleep(poll_interval_s)  # 기본 5초

        # 1. Redis에서 최신 심볼 조회
        new_symbols = await _get_symbols_from_redis(provider)

        # 2. 변경 감지
        if new_symbols == current_symbols:
            continue  # 변경 없으면 스킵

        logger.info("Symbols changed: %s → %s", current_symbols, new_symbols)

        # 3. 증분 구독 적용
        if hasattr(ingestor.client, "apply_symbols"):
            # KIS/Upbit: WebSocket 유지 + 증분 구독
            await ingestor.apply_symbols(new_symbols)
        else:
            # Binance: Ingestor 재시작
            task.cancel()
            task, ingestor = await start_ingestor(new_symbols)

        current_symbols = new_symbols
```

### 4.3 증분 구독 로직 (KIS 예시)

**파일**: [kis_client.py:166-217](../services/market-data/src/quote_pipeline/clients/kis/kis_client.py#L166-L217)

```python
async def apply_symbols(symbols: Iterable[str]):
    """
    동적 구독 변경 (WebSocket 재연결 없이)

    1. 원하는 구독 목록 생성
    2. 증분 계산 (to_add, to_remove)
    3. WebSocket 메시지 전송
    """
    desired_subs = {}
    for sym in symbols:
        metadata = symbol_service.get_metadata_by_symbol(sym)
        sub = build_subscription(sym, metadata.national, metadata.exchange)
        desired_subs[(sub.tr_id, sym)] = sub.tr_key

    # 증분 계산
    to_add, to_remove = subscription_service.calculate_changes(desired_subs)

    # 구독 해제
    for (tr_id, sym), tr_key in to_remove.items():
        await ws.send({"tr_type": "2", "tr_id": tr_id, "tr_key": tr_key})
        subscription_service.mark_unsubscribed(tr_id, sym)

    # 구독 등록
    for (tr_id, sym), tr_key in to_add.items():
        await ws.send({"tr_type": "1", "tr_id": tr_id, "tr_key": tr_key})
        subscription_service.mark_subscribed(tr_id, sym, tr_key)
```

**증분 계산 예시**:
```python
# 현재 구독: {NVDA, AAPL}
# 새로운 구독: {NVDA, TSLA}

to_add = {TSLA}       # 새로 추가할 심볼
to_remove = {AAPL}    # 제거할 심볼

# WebSocket 메시지:
# → UNREGISTER AAPL
# → REGISTER TSLA

# 최종 구독: {NVDA, TSLA}
```

---

## 5. 사용자 시나리오

### 5.1 시나리오 1: 종목 검색

**사용자 행동**:
```
사용자가 "테슬라" 검색
  ↓
Core API: /api/quotes/search?q=TSLA
```

**백엔드 동작**:
```python
# 1. Redis에서 캐시된 시세 조회
price = redis.hget("quote:US:NAS:TSLA", "price")

if not price:
    # 2. 캐시 미스: REST API로 현재가 조회 (1회)
    price = kis_rest_api.get_current_price("TSLA")
    redis.hset("quote:US:NAS:TSLA", "price", price)

# 3. active_symbols에 추가 (TTL 5분)
redis.sadd("active_symbols:kis_new", "TSLA")
redis.expire("active_symbols:kis_new", 300)  # 5분

# 4. 응답 반환
return {"symbol": "TSLA", "price": price}
```

**결과**:
- 5초 이내에 IngestorManager가 변경 감지
- TSLA 실시간 구독 시작
- 이후 시세는 WebSocket으로 실시간 수신
- 5분 후 TTL 만료 → 자동 제거

### 5.2 시나리오 2: 관심종목 추가

**사용자 행동**:
```
사용자가 "삼성전자(005930)"를 관심종목에 추가
  ↓
Core API: POST /api/watchlist {"symbol": "005930"}
```

**백엔드 동작**:
```python
# 1. DB에 저장
db.insert("watchlist", user_id=user_id, symbol="005930")

# 2. active_symbols에 영구 추가 (TTL 없음)
redis.sadd("active_symbols:kis_new", "005930")

# 3. IngestorManager 폴링 감지 (최대 5초)
# 4. KisClient.apply_symbols() 호출
# 5. WebSocket 구독 등록

# 결과: 삼성전자 실시간 시세 수신 시작
```

### 5.3 시나리오 3: 포트폴리오 편입

**사용자 행동**:
```
사용자가 "엔비디아(NVDA)" 를 포트폴리오에 편입
  ↓
Core API: POST /api/portfolio/positions {"symbol": "NVDA", "quantity": 10}
```

**백엔드 동작**:
```python
# 1. DB에 포지션 저장
db.insert("positions", user_id=user_id, symbol="NVDA", quantity=10)

# 2. active_symbols에 영구 추가
redis.sadd("active_symbols:kis_new", "NVDA")

# 3. 실시간 구독 활성화

# 결과: 포트폴리오 화면에서 실시간 수익률 계산 가능
```
### 5.4 시나리오 4: WebSocket 클라이언트 구독

**클라이언트 동작**:
```javascript
// 1. WebSocket 연결
const ws = new WebSocket('ws://api.port-rally.com/ws/quotes')

// 2. 구독 메시지 전송
ws.send(JSON.stringify({
  type: 'subscribe',
  symbols: ['NVDA', '005930', 'KRW-BTC']
}))

// 3. 실시간 시세 수신
ws.onmessage = (event) => {
  const quote = JSON.parse(event.data)
  // { symbol: 'NVDA', price: 135.50, timestamp: ... }
  updateUI(quote)
}
```

**백엔드 동작**:
```python
# WS Gateway (Core API 내부)

# 1. 세션별 구독 리스트 관리
session.subscriptions = {'NVDA', '005930', 'KRW-BTC'}

# 2. Redis pub/sub 구독
redis_pubsub.subscribe('quotes.tick')

# 3. 메시지 수신 시 필터링
async for message in redis_pubsub.listen():
    quote = json.loads(message['data'])

    # 해당 심볼을 구독한 세션에만 push
    if quote['symbol'] in session.subscriptions:
        await session.send(json.dumps(quote))
```

---

## 6. Provider별 구독 전략

### 6.1 KIS (한국투자증권)

**특징**:
- 개별 증분 구독 지원
- WebSocket 연결 유지
- TR_ID 기반 구독 (국내: H0UNCNT0, 해외: HDFSCNT0)

**증분 구독 예시**:
```python
# 기존 구독: {005930, NVDA}
# 새 구독: {005930, TSLA}

# 증분 계산
to_add = {TSLA}
to_remove = {NVDA}

# WebSocket 메시지
ws.send({"tr_type": "2", "tr_id": "HDFSCNT0", "tr_key": "DNASNVDA"})  # 해지
ws.send({"tr_type": "1", "tr_id": "HDFSCNT0", "tr_key": "DNASTSLA"})  # 등록

# 결과: {005930, TSLA}
```

**장점**:
- 최소한의 메시지만 전송 (효율적)
- WebSocket 연결 유지 (안정적)
- 무중단 구독 변경

### 6.2 Upbit

**특징**:
- 전체 재구독 방식
- WebSocket 연결 유지
- Ticker 형식 구독

**전체 재구독 예시**:
```python
# 기존 구독: {KRW-BTC, KRW-ETH}
# 새 구독: {KRW-BTC, KRW-XRP}

# WebSocket 메시지 (전체 심볼 목록 재전송)
payload = [
    {"ticket": "port-rally"},
    {"type": "ticker", "codes": ["KRW-BTC", "KRW-XRP"]}
]
await ws.send(json.dumps(payload))

# 결과: {KRW-BTC, KRW-XRP}
```

**장점**:
- 구현 단순 (Upbit API 특성에 맞음)
- WebSocket 연결 유지
- 안정적

**단점**:
- 증분이 아닌 전체 재구독 (심볼 수가 많으면 비효율)

### 6.3 Binance

**특징**:
- 증분 구독 미구현
- Ingestor 재시작 방식
- WebSocket 재연결

**재시작 방식 예시**:
```python
# 심볼 변경 감지
if new_symbols != current_symbols:
    # 1. 기존 Ingestor 종료
    task.cancel()
    await task

    # 2. 새 Ingestor 시작
    task = asyncio.create_task(
        ingestor.run_forever()
    )
```

**장점**:
- 간단한 구현

**단점**:
- 재연결 시 3-5초 시세 수신 중단
- 네트워크 오버헤드

**개선 계획**:
- Binance WebSocket API의 증분 구독 방식 조사 필요

---

## 7. 운영 가이드

### 7.1 Redis 명령어

**심볼 추가**:
```bash
# KIS 해외 주식
redis-cli SADD active_symbols:kis_new TSLA

# KIS 국내 주식
redis-cli SADD active_symbols:kis_new 000660

# Upbit 가상화폐
redis-cli SADD active_symbols:upbit KRW-XRP
```

**심볼 제거**:
```bash
redis-cli SREM active_symbols:kis_new NVDA
redis-cli SREM active_symbols:upbit KRW-BTC
```

**심볼 확인**:
```bash
# Provider별 확인
redis-cli SMEMBERS active_symbols:kis_new
redis-cli SMEMBERS active_symbols:upbit
redis-cli SMEMBERS active_symbols:binance

# 전체 심볼 확인
redis-cli SUNION \
  active_symbols:kis_new \
  active_symbols:upbit \
  active_symbols:binance
```

**Set 초기화**:
```bash
# 특정 Provider 초기화
redis-cli DEL active_symbols:kis_new

# 전체 초기화
redis-cli DEL active_symbols:kis_new active_symbols:upbit active_symbols:binance
```

### 7.2 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DYNAMIC_ENABLED` | 동적 모드 활성화 | `false` |
| `ACTIVE_SYMBOL_SET` | Redis Set 베이스 이름 | `active_symbols` |
| `ACTIVE_SYMBOL_POLL_INTERVAL` | 폴링 주기 (초) | `5` |
| `REDIS_URL` | Redis 연결 URL | (필수) |

### 7.3 로그 모니터링

**심볼 변경 로그**:
```bash
# IngestorManager 폴링 로그
docker compose logs -f market-data | grep "Symbols changed"

# 출력 예시:
# [kis_new] Symbols changed: {'NVDA', 'AAPL'} → {'NVDA', 'TSLA'}
# [kis_new] Apply: add=1 remove=1
# [KisClient][HDFSCNT0] Unsubscribed AAPL (DNYSAAPL)
# [KisClient][HDFSCNT0] Subscribed TSLA (DNASTSLA)
```

**구독 상태 확인**:
```bash
# 구독 등록 로그
docker compose logs -f market-data | grep "Subscribed"

# 출력 예시:
# [KisClient][H0UNCNT0] Subscribed 005930 (005930)
# [KisClient][HDFSCNT0] Subscribed NVDA (DNASNVDA)
```

### 7.4 문제 해결

**Q1. 심볼 추가했는데 시세가 안 들어온다**:
```bash
# 1. Redis Set 확인
redis-cli SMEMBERS active_symbols:kis_new
# TSLA가 있는지 확인

# 2. 로그 확인
docker compose logs -f market-data | grep "Symbols changed"
# 폴링 감지 확인

# 3. 구독 상태 확인
docker compose logs -f market-data | grep "TSLA"
# 구독 메시지 전송 확인
```

**Q2. 폴링이 동작 안 한다**:
```bash
# 환경변수 확인
echo $DYNAMIC_ENABLED  # true 확인
echo $REDIS_URL        # 연결 정보 확인

# Redis 연결 테스트
redis-cli PING  # PONG 응답 확인
```

**Q3. WebSocket 재연결이 자주 발생한다**:
```bash
# 로그에서 재연결 패턴 확인
docker compose logs -f market-data | grep "Connection closed"

# 원인:
# - Approval Key 만료 (24시간)
# - 네트워크 불안정
# - Provider API 제한 초과

# 해결:
# - KisWsAuthClient의 캐시 확인
# - ping_interval 조정 (기본 30초)
# - 구독 심볼 수 제한
```

---

## 8. 아키텍처 히스토리

### 8.1 v1.0: 단일 Set 방식 (Deprecated)

**사용 시기**: 2024-Q4

**구조**:
```
active_symbols  # 모든 Provider가 공유하는 단일 Set
```

**문제점**:
- Provider 구분 불가능
- KIS가 Upbit 심볼까지 처리 시도
- 심볼 충돌 및 에러 발생
- 예: `005930`(KIS 국내), `NVDA`(KIS 해외), `KRW-BTC`(Upbit) 모두 섞임

### 8.2 v2.0: Provider별 격리 (현재)

**변경 이유**:
- Provider별 독립적인 심볼 관리 필요성 인식
- WebSocket 연결 및 메시지 포맷이 Provider마다 다름
- 심볼 충돌 방지 및 명확한 책임 분리

**변경 사항**:
```
active_symbols           # (사용 안 함)
active_symbols:kis_new   # Provider별 격리
active_symbols:upbit
active_symbols:binance
```

**개선 효과**:
- ✅ Provider별 독립적인 심볼 관리
- ✅ 심볼 충돌 방지
- ✅ 명확한 책임 분리
- ✅ 각 Provider API 특성에 맞게 최적화 가능

### 8.3 증분 구독 로직 추가

**이전 (v1.0)**:
```python
# 심볼 변경 시 전체 Ingestor 재시작
if new_symbols != current_symbols:
    task.cancel()  # WebSocket 연결 종료
    await task
    task = asyncio.create_task(
        ingestor.run_forever()  # 새 연결 시작
    )
    # → 3-5초 시세 수신 중단 발생
```

**현재 (v2.0)**:
```python
# 증분 구독 (KIS, Upbit)
if hasattr(ingestor.client, "apply_symbols"):
    await ingestor.apply_symbols(new_symbols)
    # → WebSocket 연결 유지
    # → 무중단 심볼 변경
```

**변경 이유**:
- 재연결 시 시세 수신 중단 (데이터 손실)
- 고빈도 거래 환경에서 치명적
- KIS/Upbit API가 증분 구독 지원 확인

**효과**:
- ✅ 무중단 심볼 변경
- ✅ 데이터 손실 방지
- ✅ 네트워크 효율 향상

---

## 부록 A. 관련 문서

- [Market Data Pipeline](./03_marketdata_pipeline.md) - 전체 시세 파이프라인 아키텍처
- [DB Schema](./db_schema.md) - securities_master 테이블
- [KIS Provider 상세](./03_marketdata_pipeline.md#6-kis-provider-상세) - KIS 증분 구독 로직

---

## 부록 B. 심볼 자동 분류 규칙

**패턴 매칭** (빠름):
```python
if symbol.startswith("KRW-"):
    provider = "upbit"
elif symbol.lower().endswith(("usdt", "btc")):
    provider = "binance"
else:
    # DB 조회 또는 기본값 (kis_new)
```

**DB 조회** (정확):
```sql
SELECT provider FROM securities_master WHERE symbol = ?
```

**우선순위**:
1. 패턴 매칭 (빠름)
2. DB 조회 (정확)
3. 기본값 (kis_new)

---

**문서 버전**: v2.0
**최종 업데이트**: 2026-01-05
**작성자**: Port Rally Team
