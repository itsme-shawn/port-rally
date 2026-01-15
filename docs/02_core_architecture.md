# 2. 시스템 아키텍처 및 기술 스택

> 버전: v0.2.0
> 최종 수정일: 2026-01-15

## 개정 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-15 | v0.2.0 | apps/api → apps/core-api 경로 수정, 구현 현황 반영 |
| 2026-01-04 | v0.1.0 | R2DBC 전환 반영 |
| 2025-Q4 | v0.0.0 | 초기 작성 |

## 주요 아키텍처 개요
MSA (Microservice Architecture) 지향 모노레포 구조

## 모듈 요약
| **모듈명** | **기술 스택** | **핵심 역할 및 책임** | **구현 상태** |
| --- | --- | --- | --- |
| **apps/web** | Next.js | UI/UX, 온보딩, 대시보드, REST API 호출 | ✅ 구현 완료 |
| **apps/core-api** | Spring WebFlux + R2DBC | 비즈니스 로직, REST API, 인증/인가, 포트폴리오 관리 | ✅ 구현 완료 |
| **services/market-data** | Python 3.12 + asyncio | 시세 수집 및 정규화, Redis Pub/Sub 발행, 캐시 갱신 | ✅ 구현 완료 |
| **services/ai-agent** | Python (LLM) | LLM 기반 포트폴리오 분석 및 인사이트 생성 | 🔄 계획 단계 |
| **Redis** | Redis | 실시간 시세 스트림(Pub/Sub), 현재가 캐시(Hash), 구독 관리(Set) | ✅ 구현 완료 |
| **Kafka** | Apache Kafka | 비동기 작업 큐 & 이벤트 버스 (API ↔ AI Agent) | 🔄 계획 단계 |
| **PostgreSQL** | PostgreSQL 16 + R2DBC | 사용자/포트폴리오 데이터 영구 저장 (19개 테이블) | ✅ 구현 완료 |

## 모듈별 설명

### 수신기(ingestor)
* 외부벤더로부터의 시세 입수 모듈
* Provider별 Redis Set (`active_symbols:kis_new`, `active_symbols:upbit`, `active_symbols:binance`)을 정기적으로 읽어 구독 목록을 최신 상태로 유지
* 변경 감지 시:
  - **KIS/Upbit**: `apply_symbols()` 메서드로 증분 구독 (WebSocket 연결 유지)
  - **Binance**: ingestor 재시작 (전체 재구독)
* Normalize된 틱을 Redis pub/sub `quotes.tick` 에 발행
* Hexagonal Architecture 기반으로 설계 (Ports & Adapters)
* 4가지 실행 모드 지원: single-static, multi-static, single-dynamic, multi-dynamic

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
    - **Set (Provider별 격리):**
      - `active_symbols:kis_new` (KIS 구독 심볼)
      - `active_symbols:upbit` (Upbit 구독 심볼)
      - `active_symbols:binance` (Binance 구독 심볼)
      - `active_symbols` (레거시, 사용 안 함)

### 메시징 및 비동기 처리

- Redis (Speed): apps/core-api와 market-data 사이의 실시간 시세(Quotes) 처리. 데이터가 유실되어도 다음 틱이 바로 오면 되는 성격이므로 Redis Pub/Sub을 선택함.

- Kafka (Reliability, 계획): apps/core-api와 ai-agent 사이의 분석 작업(Jobs) 처리를 담당. 분석 요청은 유실되면 안 되고, 트래픽 폭주 시 처리를 지연시키더라도 안전하게 보관해야 하므로 Kafka를 선택할 예정.

### core-api 상세 (`apps/core-api/`)

- **기술:** Spring Boot 3.5.8 + WebFlux + R2DBC + PostgreSQL 16
- **구현 현황:**
  - ✅ **REST API Layer**
    - OAuth2 소셜 로그인 (Google, Kakao, Naver, Apple)
    - JWT 기반 인증/인가
    - 사용자 관리 (회원가입, 프로필, 약관 동의)
    - 포트폴리오 CRUD (다중 포트폴리오, 포지션 관리)
    - OCR 이미지 업로드 및 자동 종목 인식
    - 현재가 조회 (Redis `quote:<symbol>`)
    - active_symbols 관리 (검색/관심/포트폴리오 추가 시 TTL 기반 추가)
  - 🔄 **WebSocket Layer (계획 단계)**
    - Redis `quotes.tick` 구독
    - 실시간 시세 전송 (Filtering & Push)
    - 세션별 심볼 구독/구독해제 관리
    - Rate limiting
  - 🔄 **AI Agent 연동 (계획 단계)**
    - Kafka를 통한 분석 작업 적재
    - 분석 완료 상태 조회
- **주요 도메인:**
    - User, SocialAccount, UserPreference
    - Portfolio, Position, PortfolioMetric
    - Asset, AssetMetric, AssetAiInsight
    - UploadedImage, OcrResult, OcrDetectedPosition
    - NewsArticle, NotificationLog, AuditLog
- **데이터베이스:**
    - 총 19개 테이블, Flyway 8개 마이그레이션
    - R2DBC Reactive 지원 (JPA → R2DBC 전환 완료)
    - PostgreSQL ENUM → VARCHAR 변환 완료

## 구조도
```
apps/web (Next.js)              apps/core-api (Spring WebFlux)
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
    · pub/sub: quotes.tick                 (실시간 틱 스트림)
    · hash:   quote:<symbol>               (현재가 캐시)
    · set:    active_symbols:kis_new       (KIS 구독 심볼)
    · set:    active_symbols:upbit         (Upbit 구독 심볼)
    · set:    active_symbols:binance       (Binance 구독 심볼)

  - Kafka
    · Agent Job Queue, 로그 용도

  - PostgreSQL
    · 사용자, 포트폴리오, 관심종목, AI 분석 결과 저장

```

## 디렉토리 구조 요약 (모노레포)
```
port-rally/
├── apps/                           # 사용자 대면 애플리케이션
│   ├── core-api/                   # Spring WebFlux (백엔드 코어/비즈니스 로직)
│   └── web/                        # Next.js (프론트엔드)
├── services/                       # 백엔드 서비스들
│   ├── market-data/                # 시세 파이프라인 (Python)
│   └── ai-agent/                   # AI 에이전트 (Python)
├── packages/                       # 공유 라이브러리
├── infrastructure/                 # 인프라 설정
└── docs/                           # 문서
```
