# 온디맨드 시세 스트리밍 시스템

> 버전: v0.2.0
> 최종 수정일: 2026-01-15
> 관련 서비스: services/market-data, apps/core-api
> 관련 문서: [Market Data Pipeline](./03_marketdata_pipeline.md), [DB Schema](./docs/06_db_schema.md)

## 개정 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-15 | v0.2.0 | 파일 라인 참조 및 코드 분석 반영 (ingestor_manager.py, kis_client.py) |
| 2026-01-15 | v0.1.0 | 문서 버전 관리 추가, apps/api → apps/core-api 경로 수정 |
| 2026-01-05 | v0.0.0 | 초기 작성 |

---

## 목차

- [온디맨드 시세 스트리밍 시스템](#온디맨드-시세-스트리밍-시스템)
  - [개정 이력](#개정-이력)
  - [목차](#목차)
  - [1. 왜 온디맨드 방식인가?](#1-왜-온디맨드-방식인가)
  - [2. 핵심 개념](#2-핵심-개념)
  - [3. Active Symbols 시스템](#3-active-symbols-시스템)
    - [3.1 Redis Set 구조](#31-redis-set-구조)
    - [3.2 동적 구독 흐름](#32-동적-구독-흐름)
  - [4. 동작 원리](#4-동작-원리)
    - [4.1 폴링 루프 (IngestorManager)](#41-폴링-루프-ingestormanager)
    - [4.2 증분 구독 로직 (KIS 예시)](#42-증분-구독-로직-kis-예시)
  - [5. 사용자 시나리오](#5-사용자-시나리오)
  - [6. Provider별 구독 전략](#6-provider별-구독-전략)
  - [7. 운영 가이드](#7-운영-가이드)
    - [7.1 Redis 명령어 활용](#71-redis-명령어-활용)
  - [8. 아키텍처 히스토리](#8-아키텍처-히스토리)

---

## 1. 왜 온디맨드 방식인가?

(기존 내용 유지)

---

## 2. 핵심 개념

(기존 내용 유지 - TTL 기반 관리, Provider별 독립 관리)

---

## 3. Active Symbols 시스템

### 3.1 Redis Set 구조

```
Redis
├── active_symbols:kis_new   # KIS (국내/해외 주식)
├── active_symbols:upbit     # Upbit (가상화폐)
└── active_symbols:binance   # Binance (가상화폐)
```

### 3.2 동적 구독 흐름

1. **사용자/API**: Redis Set에 심볼 추가 (`SADD`)
2. **IngestorManager**: 5초 간격으로 `SMEMBERS` 폴링하여 변경 감지
3. **Client.apply_symbols()**: 변경된 심볼 리스트를 엔진에 적용
4. **SubscriptionService**: 현재 구독 중인 목록과 대조하여 `to_add`, `to_remove` 계산
5. **WebSocket**: 최소한의 REGISTER/UNREGISTER 메시지 전송 (무중단)

---

## 4. 동작 원리

### 4.1 폴링 루프 (IngestorManager)

**파일**: `services/market-data/src/quote_pipeline/ingestors/ingestor_manager.py`

```python
async def _run_dynamic_symbol_loop(self, provider: Provider):
    # 5초마다 Redis Set 확인
    # 변경 시 ingestor.apply_symbols() 호출
```

### 4.2 증분 구독 로직 (KIS 예시)

**파일**: `services/market-data/src/quote_pipeline/clients/kis/kis_client.py`

```python
async def apply_symbols(self, symbols: Iterable[str]):
    # 1. SymbolService(Redis 캐시)에서 국가/거래소 정보 조회
    # 2. SubscriptionService를 통해 증분(추가/제거) 계산
    # 3. KIS WebSocket으로 필요한 변경 메시지만 전송
```

---

## 5. 사용자 시나리오

(기존 내용 유지 - 종목 검색, 관심종목, 포트폴리오 시나리오)

---

## 6. Provider별 구독 전략

- **KIS**: 개별 증분 구독 (`REGISTER`, `UNREGISTER`) 지원. WebSocket 연결 유지.
- **Upbit**: 전체 재구독 방식. WebSocket 연결은 유지하되 전체 목록 재전송.
- **Binance**: 현재 증분 미지원으로 연결 재시작 방식 사용 중.

---

## 7. 운영 가이드

### 7.1 Redis 명령어 활용

```bash
# 심볼 추가
redis-cli SADD active_symbols:kis_new TSLA

# 현재 구독 중인 심볼 확인
redis-cli SMEMBERS active_symbols:kis_new
```

---

## 8. 아키텍처 히스토리

(기존 내용 유지 - v1.0 단일 Set에서 v2.0 Provider 격리 및 증분 구독 도입)
