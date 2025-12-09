# 2. 시스템 아키텍처 및 기술 스택

## 주요 아키텍처 개요
MSA (Microservice Architecture) 지향 모노레포 구조

## 모듈 요약
| **모듈명** | **기술 스택** | **핵심 역할 및 책임** |
| --- | --- | --- |
| **apps/web** | Next.js | UI/UX, 초기 데이터 조회(REST), 실시간 시세 시각화(WebSocket) |
| **apps/api** | Spring WebFlux | 비즈니스 로직, WS 시세 중계, **Kafka 프로듀서(AI 분석 요청 발행)** |
| **services/market-data** | Python | 시세 수집 및 정규화, Redis Pub/Sub 발행(실시간), 캐시 갱신 |
| **services/ai-agent** | Python (LLM) | **Kafka 컨슈머(분석 작업 처리)**, 포트폴리오 분석 결과 DB 저장 |
| **Redis** | Redis | 실시간 시세 스트림(Pub/Sub), 현재가 캐시(Hash), 구독 관리(Set) |
| **Kafka** | Apache Kafka | **비동기 작업 큐 & 이벤트 버스 (API ↔ AI Agent)** |
| **PostgreSQL** | PostgreSQL | 사용자/포트폴리오 데이터, AI 분석 결과 영구 저장 |

## 모듈별 설명

### 수신기(ingestor)
* 외부벤더로부터의 시세 입수 모듈
* active_symbols를 정기적으로 읽어 구독 목록을 최신 상태로 유지
* 변경 감지 시 종목 구독 재설정
* Normalize된 틱을 Redis pub/sub quotes.tick 에 발행
* 장애 시 active_symbols 전체 재구독

### 데이터베이스 및 캐싱

- **PostgreSQL (RDB):**
    - **Core Data:** 사용자, 포트폴리오, 알림 등 비즈니스 데이터.
    - **AI Results:** AI가 생성한 종목 분석, 리포트, 리스크 스코어 결과물 (**AI Agent가 직접 Write**).
    - *(참고: 초기에는 시세 데이터의 영구 저장보다는 현재가 위주로 운영하며, 차트 데이터는 외부 API 의존 또는 필요시 추후 TimescaleDB 도입)*
- **Redis (In-Memory Hub):**
    - **Cache:** `quote:<symbol>` (REST용 현재가 조회).
      - 현재가만 저장하고 과거 데이터는 저장하지 않음
      - `quote:<symbol>`에 price, ts 저장
    - **Pub/Sub:** `quotes.tick` (Ingestor → API 실시간 시세 스트림).
    - **Set:** `active_symbols` (구독 관리).

### 메시징 및 비동기 처리

- Redis (Speed): apps/api와 market-data 사이의 실시간 시세(Quotes) 처리. 데이터가 유실되어도 다음 틱이 바로 오면 되는 성격이므로 Redis Pub/Sub을 선택함.

- Kafka (Reliability): apps/api와 ai-agent 사이의 분석 작업(Jobs) 처리를 담당. 분석 요청은 유실되면 안 되고, 트래픽 폭주 시 처리를 지연시키더라도 안전하게 보관해야 하므로 Kafka를 선택함.

### core-api 상세 (`apps/api/`)

- **기술:** Spring WebFlux (Reactive Framework).
- **역할:**
  - **REST layer**
    - 클라이언트 요청 처리 (REST) 및 인증/인가.
    - 코어 비즈니스 로직 (포트폴리오 분석, 시세 sub ..)
    - Redis `quote:<symbol>`에서 현재가 조회
    - 검색/관심/포폴 추가 등의 이벤트 발생 시 해당 종목을 active_symbols에 TTL 기반 추가
    - active_symbols 정책의 최종 책임자는 API Server
    - ai-agent 서비스 관련 요청 시 kafka에 작업 적재.
  - **WebSocket layer(WebSocket Gateway):**
    - 각 WebSocket 세션 별 심볼 구독/구독해제(sub/unsub) 관리
    - Redis `quotes.tick`을 구독하고, 클라이언트(web)과 연결된 세션 중 해당 종목을 보고 있는 유저에게만 시세 websocket 전송 (Filtering & Push).
    - 세션별 rate limit 
- **주요 서비스:**
    - `PortfolioService`: 자산 CRUD 및 보유 현황 계산.
    - `QuoteStreamService`: Redis Pub/Sub 연동 및 WebSocket 세션 관리.
    - `AiJobService`: 분석 요청 큐잉 및 완료 상태 조회.

## 구조도
```
apps/web (Next.js)              apps/portrally-core-api (Spring WebFlux)
        \                                 |
         \--- REST / WebSocket -----------|
                                           \
                                            \  gRPC / Redis / Kafka
                                             v

                              services/market-data (Python)
                              ├─ Subscription Manager
                              │    - Redis active_symbols 기반 종목시세 구독 관리
                              ├─ Ingestors
                              │    - Upbit / Binance / KIS 실시간 시세 수신
                              ├─ Redis pub/sub
                              │    - quotes.tick (Normalize된 틱 이벤트 실시간 publish)     
                              ├─ Redis Cache Update (Quote 현재가 갱신)
                              └─   - quote:<symbol> 캐시값 업데이트



                              services/ai-agent
                              ├─ Core API로부터 Job 수신 (Kafka / Redis 큐 등)
                              ├─ LLM 기반 포트폴리오/리스크 분석
                              └─ 결과를 DB/Redis에 저장


Infra:
  - Redis
    · pub/sub: quotes.tick        (실시간 틱 스트림)
    · hash:   quote:<symbol>      (현재가 캐시)
    · set:    active_symbols      (거래소 구독 대상 심볼)

  - Kafka
    · Agent Job Queue, 로그 용도

  - PostgreSQL
    · 사용자, 포트폴리오, 관심종목, AI 분석 결과 저장

```

## 디렉토리 구조 요약 (모노레포)
```
port-rally/
├── apps/                           # 사용자 대면 애플리케이션
│   ├── portrally-core-api/         # Spring WebFlux (백엔드 코어/비즈니스 로직)
│   └── web/                        # Next.js (프론트엔드)
├── services/                       # 백엔드 서비스들
│   ├── market-data/                # 시세 파이프라인 (Python)
│   └── ai-agent/                   # AI 에이전트 (Python)
├── packages/                       # 공유 라이브러리
├── infrastructure/                 # 인프라 설정
└── docs/                           # 문서
```
