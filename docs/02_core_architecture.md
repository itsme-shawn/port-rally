# 2. 시스템 아키텍처 및 기술 스택

## 주요 아키텍처 개요
MSA (Microservice Architecture) 지향 모노레포 구조. 실시간 데이터 처리와 비동기 통신을 위해 **Reactive Programming** 모델을 적극 활용. 

## 기술 스택 요약

| 모듈 | 기술 스택 | 주요 역할 |
| :--- | :--- | :--- |
| **프론트엔드 (Web)** | **Next.js** (SSR + CSR), TypeScript, Tailwind CSS, Zustand | SEO 최적화, 대시보드 초기 로딩 속도, WebSocket 실시간 처리 |
| **프론트엔드 (App)** | React Native (RN) **(예정)** 또는 Flutter | 모바일 앱 지원 (추후) |
| **백엔드 (Core API)** | **Spring WebFlux** (Java), R2DBC | BFF 역할 (REST + WebSocket), 비즈니스 로직, DB 통신 |
| **시세 파이프라인** | **Python**, Kafka, TimescaleDB, Redis | 원시 데이터 수집, 가공, 실시간 분배 (고성능/실시간 처리) |
| **AI 에이전트** | **Python** (FastAPI), LLM (Claude/GPT), Vector DB (Chroma/Pinecone), RAG | 포트폴리오 분석, 자연어 리포트 생성, 리밸런싱 제안 |

## 데이터베이스 및 캐싱
* **Postgres (RDB):** 사용자, 계좌, 포지션, 알림 등 OLTP (Transactional) 데이터 저장.
* **TimescaleDB (PostgreSQL 기반):** 장기 시계열 데이터 저장 (과거 시세, 차트, 백테스팅). => 추후 확장
* **Redis:** 초저지연 캐싱 (현재가 스냅샷), 세션 관리, **Pub/Sub (실시간 분배)**.

## 메시징 및 비동기 처리
* **Kafka (또는 Redis Streams):** 시세 데이터 수집-가공 계층 간 **대량 데이터 버퍼링 및 부하 분리** (Decoupling).
* **Redis Pub/Sub:** 가공된 시세 데이터를 실시간 채널에 발행하여 WebSocket 서버로 전달.

## API 서버 상세 (`apps/api/`)
* **기술:** Spring WebFlux (Reactive Framework).
* **역할:** 비즈니스 로직 처리, DB/다른 서비스(AI, Market Data)와의 연동, **WebSocket 연결 관리** (`WebSocketHandler.java`).
* **주요 서비스:** `PortfolioService`, `QuoteStreamService`, `InsightService`, `NewsService`, `AlertService`.

## 구조도
```
apps/web (Next.js)         apps/api (WebFlux)
        \                         |
         \--- WebSocket/REST -----|
                                  v
                          services/market-data (Python)
                          ├─ Subscription Manager
                          ├─ Ingestors: Upbit / Binance / KIS
                          ├─ Sinks: Stdout / Redis PubSub / Kafka(확장)
                          └─ Pub/Sub → Redis/Kafka → API/Web WS 팬아웃

Infra: Redis | Kafka | PostgreSQL
```

## 디렉토리 구조 요약 (모노레포)
```
port-rally/
├── apps/                           # 사용자 대면 애플리케이션
│   ├── portrally-core-api/         # Spring WebFlux (백엔드 코어/비즈니스 로직)
│   └── web/                        # Next.js (프론트엔드)
├── services/                       # 백엔드 서비스들
│   ├── market-data/                # 시세 파이프라인 (Python)
│   └── agent/                      # AI 에이전트 (Python)
├── packages/                       # 공유 라이브러리
├── infrastructure/                 # 인프라 설정
└── docs/                           # 문서
```
