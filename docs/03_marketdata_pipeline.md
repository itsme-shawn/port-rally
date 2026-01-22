# Market Data Pipeline 아키텍처

> 버전: v0.1.0
> 최종 수정일: 2026-01-15
> 관련 서비스: services/market-data

## 개정 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-15 | v0.1.0 | 문서 버전 관리 추가 |
| 2026-01-04 | v0.0.0 | 초기 작성 (Hexagonal Architecture 리팩토링 반영) |

---

## 목차

1. [개요](#1-개요)
2. [전체 아키텍처](#2-전체-아키텍처)
3. [레이어별 상세 설명](#3-레이어별-상세-설명)
4. [실행 모드](#4-실행-모드)
5. [데이터 흐름](#5-데이터-흐름)
6. [KIS Provider 상세](#6-kis-provider-상세)
7. [실행 가이드](#7-실행-가이드)
8. [리팩토링 히스토리](#8-리팩토링-히스토리)

---

## 1. 개요

### 1.1 목적

Market Data Pipeline은 여러 거래소(KIS, Upbit, Binance)의 실시간 시세 데이터를 수집하여 Redis에 저장하는 시스템이다

### 1.2 핵심 기능

- **다중 Provider 지원**: KIS(국내/해외 주식), Upbit(암호화폐), Binance(암호화폐)
- **동적 심볼 관리**: Redis Set을 통한 런타임 심볼 추가/제거
- **실시간 시세 발행**: Redis Pub/Sub 및 Hash 저장
- **재연결 및 복구**: WebSocket 연결 실패 시 자동 재연결

### 1.3 기술 스택

- **언어**: Python 3.12
- **프레임워크**: asyncio, websockets
- **데이터베이스**: PostgreSQL (종목 마스터)
- **캐시**: Redis (시세 저장, Pub/Sub, 동적 심볼 관리, 메타데이터 캐싱)

---

## 2. 전체 아키텍처

### 2.1 레이어 구조

```
┌─────────────────────────────────────────────────────────┐
│                    BaseIngestor                          │
│                 (Thin Orchestrator)                      │
└─────────────────────────────────────────────────────────┘
         │              │              │              │
         ↓              ↓              ↓              ↓
  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
  │  Client  │  │   Parser    │  │  Mapper  │  │Publisher │
  │ (입력포트) │  │  (파싱)     │  │  (변환)   │  │(출력포트) │
  └──────────┘  └─────────────┘  └──────────┘  └──────────┘
         │              │              │              │
         ↓              ↓              ↓              ↓
    WebSocket      DTO 추출    UniQuoteDto    Redis/Stdout
```

### 2.2 디렉토리 구조

```
quote_pipeline/
├── clients/                    # 외부 시스템 클라이언트 (입력 포트)
│   ├── base_client.py          # BaseClient (abstract)
│   ├── kis/
│   │   ├── kis_client.py       # KisClient (WebSocket lifecycle)
│   │   ├── kis_auth_client.py  # 인증 클라이언트
│   │   ├── kis_ws_client.py    # WebSocket 메시지 빌더
│   │   ├── kis_rest_client.py  # REST API 클라이언트
│   │   └── kis_config.py       # KIS 설정
│   ├── upbit/
│   │   └── upbit_client.py     # UpbitClient
│   └── binance/
│       └── binance_client.py   # BinanceClient
│
├── parsers/                    # 메시지 파싱 레이어
│   ├── message_parser.py       # MessageParser (abstract)
│   ├── kis_message_parser.py   # KIS 파서
│   ├── upbit_message_parser.py # Upbit 파서
│   └── binance_message_parser.py # Binance 파서
│
├── mappers/                    # DTO → Domain Event 변환
│   ├── base_mapper.py          # BaseMapper (abstract)
│   ├── kis_quote_mapper.py     # KIS 매퍼
│   ├── upbit_quote_mapper.py   # Upbit 매퍼
│   └── binance_quote_mapper.py # Binance 매퍼
│
├── domain/                     # 도메인 객체 (DTOs)
│   ├── uni_quote_dto.py        # 통합 시세 DTO
│   └── kis_*_dto.py            # Provider별 DTOs
│
├── services/                   # 재사용 가능한 비즈니스 로직
│   ├── symbol_service.py       # 심볼 관리 (Redis 캐싱, DB 로드)
│   └── subscription_service.py # 구독 상태 추적
│
├── publishers/                 # 출력 포트 (Sinks)
│   ├── base_publisher.py       # Publisher (abstract)
│   ├── redis_publisher.py      # RedisPublisher
│   └── stdout_publisher.py     # StdoutPublisher
│
├── ingestors/                  # 파이프라인 조립 및 실행
│   ├── base_ingestor.py        # BaseIngestor (orchestrator)
│   ├── ingestor_factory.py     # 팩토리 함수
│   └── ingestor_manager.py     # 4가지 실행 모드 관리
│
├── db/                         # 데이터베이스 연결
│   └── connection.py           # PostgreSQL 연결
│
├── stores/                     # 상태 저장소
│   ├── quote_store.py          # Redis 시세 저장 (Sidecar)
│   └── active_symbols_store.py # (Legacy)
│
├── utils/                      # 유틸리티
│   └── trading_hours.py        # 거래 시간 체크
│
├── config.py                   # 설정 관리
├── main.py                     # CLI entry point
└── manage.py                   # 운영 유틸리티
```

---

## 3. 레이어별 상세 설명

### 3.1 Domain Layer

**기능**: 시스템의 핵심 도메인 객체 정의 (`UniQuoteDto` 등)

### 3.2 Clients Layer

**기능**: 외부 시스템과의 통신 (WebSocket, REST API). `BaseClient`를 상속받아 각 거래소별 클라이언트 구현.

### 3.3 Parsers Layer

**기능**: raw 메시지 → DTO 변환. KIS의 경우 국내/해외/응답 메시지를 구분하여 파싱.

### 3.4 Mappers Layer

**기능**: Provider별 DTO → `UniQuoteDto` 변환 (정규화).

### 3.5 Services Layer

**기능**: 재사용 가능한 비즈니스 로직

#### SymbolService

- **역할**: 심볼의 메타데이터(국가, 거래소)를 Redis에 캐싱하고 조회
- **동작**:
  1. Startup 시 DB(`assets_master`)에서 모든 심볼 정보를 읽어 Redis(`symbol_metadata:{symbol}`)에 JSON으로 저장
  2. 런타임에는 Redis 캐시에서 즉시 조회 (DB 부하 감소)
- **장점**: 분산 환경에서 여러 ingestor 프로세스가 동일한 메타데이터 캐시 공유

#### SubscriptionService

- **역할**: WebSocket 구독 상태(TR_ID, TR_KEY) 추적
- **핵심 기능**: `calculate_changes(desired_subs)`를 통해 현재 구독 상태와 목표 상태를 비교하여 추가/제거할 목록 산출

### 3.6 Publishers Layer

**책임**: 도메인 이벤트를 외부로 발행 (Redis Pub/Sub `quotes.tick` 등)

---

## 4. 실행 모드

(기존 내용 유지 - single/multi, static/dynamic 4가지 조합)

---

## 5. 데이터 흐름

### 5.1 정적 모드 (Static Symbol)
- 초기 지정된 심볼로 고정 구독 실행

### 5.2 동적 모드 (Dynamic Symbol)
- **IngestorManager**가 Redis `active_symbols:{provider}` Set을 5초마다 폴링
- 변경 감지 시 `apply_symbols()`를 호출하여 무중단 구독 갱신

---

## 6. KIS Provider 상세

(기존 상세 내용 유지하되 최신 코드 구조 반영)

---

## 7. 실행 가이드

(기존 내용 유지)

---

## 8. 리팩토링 히스토리

(기존 내용 유지)