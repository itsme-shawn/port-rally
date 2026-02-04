# PortRally

AI 기반 투자 포트폴리오 분석 서비스

> 본 서비스는 정보 제공 목적의 포트폴리오 분석 도구이며, 투자 권유나 매매 추천을 제공하지 않습니다.

## 주요 기능

- **실시간 대시보드**: 보유 포트폴리오 히트맵, 주요 변동 종목 확인
- **멀티 마켓 지원**: 국내/해외 주식, 암호화폐 등 다양한 자산 통합 관리
- **AI 인사이트**: 리스크 점수, 집중도 분석, 자연어 리포트 생성 (예정)
- **스마트 알림**: 가격 알림, 변동성 경고, 뉴스 기반 알림 (예정)
- **OCR 인식**: 증권사 스크린샷에서 자동으로 보유 종목 인식

## 기술 스택

### 백엔드
- **Core API**: Spring Boot 3.5 + WebFlux + R2DBC
- **Market Data**: Python 3.12 + asyncio (실시간 시세)
- **AI Agent**: Python + LLM (예정)

### 프론트엔드
- **Web**: Next.js 16 + React 19 + TailwindCSS 4
- **상태 관리**: Zustand + TanStack Query

### 인프라
- **데이터베이스**: PostgreSQL 16 (Flyway 마이그레이션)
- **캐시 & 스트리밍**: Redis (Pub/Sub, Hash)
- **메시지 큐**: Kafka (예정)

## 빠른 시작

### 사전 요구사항
- Docker & Docker Compose
- Python 3.12 (로컬 개발 시)
- [uv](https://astral.sh/uv) (Python 패키지 매니저)

### 1. 환경 설정

프로젝트 루트에 `.env.local` 파일 생성 (또는 `.env.example에서 복사):

```bash
cp .env.example .env.local
# .env.local 파일을 열어 API 키 및 설정 편집
```

### 2. Docker로 서비스 시작

```bash
# 전체 서비스 시작 (Redis, PostgreSQL, Core API, Market Data)
docker compose -f docker-compose.dev.yml up -d

# 로그 확인
docker compose logs -f

# 서비스 중지
docker compose down
```

서비스 접속 주소:
- Core API: `http://localhost:8080`
- Web UI: `http://localhost:3000` (별도 실행 필요, 아래 참조)
- Redis: `localhost:6379`
- PostgreSQL: `localhost:5432`

### 3. Web 실행 (개발 모드)

```bash
cd apps/web
npm install
npm run dev
```

### 4. 로컬 실행

#### Core API
```bash
./run-core-api-local.sh
```

#### Market Data Service
```bash
# Python 3.12 설치 및 가상환경 생성
cd services/market-data
uv venv --python 3.12
source .venv/bin/activate
uv sync

# 시세 수집 서비스 실행
./run-market-data-local.sh
```

## 프로젝트 구조

```
port-rally/
├── apps/
│   ├── core-api/          # Spring Boot 백엔드 (REST API, WebSocket 예정)
│   └── web/               # Next.js 프론트엔드
├── services/
│   ├── market-data/       # Python 실시간 시세 파이프라인
│   └── ai-agent/          # LLM 기반 분석 (예정)
├── docs/                  # 아키텍처 & 설계 문서
└── docker-compose.*.yml   # Docker 설정 파일
```

## 아키텍처 개요

```
┌─────────────┐
│   Next.js   │
│   (Web UI)  │
└──────┬──────┘
       │ REST API
       ↓
┌─────────────────────────────┐
│  Spring Boot (Core API)     │
│  - 사용자 & 포트폴리오 관리  │
│  - OAuth2 인증               │
│  - 가격 조회 (Redis)         │
└──────┬─────────────────┬────┘
       │                 │
       ↓                 ↓
┌─────────────┐   ┌─────────────┐
│  PostgreSQL │   │    Redis    │
│  (RDB)      │   │  Pub/Sub +  │
└─────────────┘   │  Cache      │
                  └──────▲──────┘
                         │
                         │ quotes.tick
                  ┌──────┴──────┐
                  │ Market Data │
                  │  (Python)   │
                  │ KIS/Upbit/  │
                  │  Binance    │
                  └─────────────┘
```

### 핵심 컴포넌트

- **Core API**: 비즈니스 로직, 인증, 포트폴리오 관리, 가격 조회
- **Market Data**: 실시간 시세 수집 (한국투자증권, 업비트, 바이낸스)
- **Redis**:
  - Pub/Sub을 통한 실시간 시세 스트리밍 (`quotes.tick`)
  - 최신 가격 캐시 (`quote:<symbol>`)
  - 제공자별 구독 심볼 관리
- **PostgreSQL**: 사용자 데이터, 포트폴리오, 포지션, AI 분석 결과

## 문서

상세 문서는 [docs](./docs) 디렉토리에서 확인:

- [01_project_summary.md](./docs/01_project_summary.md) - 프로젝트 목표 및 KPI
- [02_core_architecture.md](./docs/02_core_architecture.md) - 시스템 아키텍처
- [03_marketdata_pipeline.md](./docs/03_marketdata_pipeline.md) - 시세 파이프라인 상세
- [04_ondemand_symbol_streaming.md](./docs/04_ondemand_symbol_streaming.md) - 동적 심볼 구독
- [06_db_schema.md](./docs/06_db_schema.md) - 데이터베이스 스키마

## 실행 스크립트

- `run-core-api-local.sh` - Core API 로컬 실행
- `run-market-data-local.sh` - Market Data 서비스 로컬 실행
- `run-web-local.sh` - Web 로컬 실행
- `init-db.sh` - PostgreSQL 데이터베이스 초기화
- `init-redis.sh` - Redis 테스트 데이터 초기화
