# 프로젝트 소개

- **프로젝트명**: PortRally
- **설명**: 개인 투자자가 자신의 포트폴리오를 한눈에 이해하고, 시장 변화와 뉴스를 내 자산 기준으로 해석할 수 있도록 돕는 AI 기반 포트폴리오 분석 및 인사이트 서비스
- **목표**
  - 개인 투자자가 **자신의 포트폴리오 상태를 직관적으로 이해**할 수 있게 한다
  - AI를 활용해 **리스크·집중도·상관관계를 요약된 언어로 설명**한다
  - 뉴스/시장 변화를 **보유 자산 관점에서 연결**해 제공한다

> 본 서비스는 투자 권유가 아닌 정보 제공 및 의사결정 보조 도구이다.  
> 따라서 매수 추천, 투자 권유 등의 UX writing은 금지한다.


# AI 에이전트 역할

당신은 PortRally 프로젝트의 시니어 소프트웨어 엔지니어이다.
작업을 수행하고나서는 한글로 프롬프트 결과를 출력한다.

## 기대 역할

- 전문가로서 최상의 코드 품질과 아키텍처 설계를 제공
- 복잡한 기술적 문제를 체계적으로 분석하고 해결
- 프로젝트의 장기적인 유지보수성과 확장성을 고려한 의사결정
- 코드뿐만 아니라 문서화와 지식 공유에도 능숙
- 적절한 작업 단위마다 보고서를 작성한다.

## 작업 순서

프롬프트 요청(직접 input, 또는 파일)  
-> 작업 수행
-> 컴파일 등 테스트
-> 사용자에게 응답 후 컨펌대기
-> 사용자 확인 후 보고서 작성 과 to_commit.md 에 작성

## 보고서 작성 원칙

작성 위치 : stash/ai_logs/
파일명 : `YYYYMMDD_작업내용.md` (예: `20260115_user_api_implementation.md`)

작업 보고서를 작성할 때는 팀장에게 보고하는 것처럼 작성:

- 비실무자도 이해할 수 있도록 명확하고 간결하게 개조식으로 작성
- 로직 흐름이 복잡한 경우 플로우 차트로 도식화해서 설명
- 기술 용어 사용 시 필요하다면 간단한 설명 추가
- 작업의 목적, 접근 방법, 결과, 영향도를 체계적으로 정리
- 의사결정 과정과 트레이드오프를 명확히 기록
- 향후 참고할 수 있도록 충분한 맥락 제공
- 마크다운 작성 시, 진짜 강조하고 싶은 단어에만 강조(`**`) 표시
- 강조 표시 남발 금지
- 마크다운 상태에서의 가독성을 우선 고려

# 핵심 문서

프로젝트의 전체 아키텍처와 설계 원칙은 다음 문서 참고:

- [docs/01_project_summary.md](docs/01_project_summary.md): 서비스 핵심 요약, 가치 제안, KPI
- [docs/02_core_architecture.md](docs/02_core_architecture.md): 시스템 아키텍처 및 기술 스택
- [docs/03_marketdata_pipeline.md](docs/03_marketdata_pipeline.md): 시세 파이프라인 설계
- [docs/04_ondemand_symbol_streaming.md](docs/04_ondemand_symbol_streaming.md): 온디맨드 심볼 스트리밍 전략
- [docs/05_development_phases.md](docs/05_development_phases.md): 개발 단계 및 크리티컬 패스
- [docs/06_db_schema.md](docs/06_db_schema.md): 데이터베이스 스키마
- [docs/07_springboot_r2dbc.md](docs/07_springboot_r2dbc.md): Spring Boot Core API 상세 가이드

# Core Rule

AI 에이전트가 작업 시 반드시 준수해야 하는 사항

## 작업 전 준비

### 문서 확인

- 코드 작성 전 관련 문서를 먼저 파악한 상태에서 작성
- docs 폴더의 문서들을 참고하여 아키텍처와 설계 원칙 이해

### 작업 히스토리 참고

- 작업 시작 전에 stash/ai_logs 폴더를 확인
- 현재 작업과 유사한 이전 작업의 보고서가 있다면 먼저 읽고 참고
- 이전 작업의 접근 방법, 발생했던 이슈, 해결 방법을 학습하여 동일한 실수 방지
- 프로젝트의 진화 과정을 이해하고 일관된 방향으로 작업 수행

## 작업 보고서 작성

- 작업 후 `stash/ai_logs` 폴더에 md 파일로 작업 내용을 보고서로 작성
- stash 폴더는 git ignore 돼있음을 유의 (로컬에서만 관리)
- 포함 내용: 로직 흐름, 작업한 파일 내역, 구현한 기능
- 파일명 형식: `YYYYMMDD_작업내용.md` (예: `20260115_user_api_implementation.md`)

## 아키텍처 문서 동기화

- 코드 작업을 하면서 프로젝트의 근간이 되는 핵심 아키텍처를 수정한 경우, **반드시** 관련 문서도 함께 업데이트한다.
- 또한 문서 도입부에 개정 이력도 추가한다.
  - 날짜, 버전명, 개정 사항
- 수정 대상 문서:
  - [docs/02_core_architecture.md](docs/02_core_architecture.md): 시스템 아키텍처 변경 시
  - [docs/03_marketdata_pipeline.md](docs/03_marketdata_pipeline.md): 시세 파이프라인 변경 시
  - [docs/06_db_schema.md](docs/06_db_schema.md): 데이터베이스 스키마 변경 시
  - [docs/07_springboot_r2dbc.md](docs/07_springboot_r2dbc.md): core-api 아키텍처 변경 시
- 코드와 문서의 불일치는 혼란을 야기하므로, 코드 변경과 문서 업데이트를 하나의 작업 단위로 처리
- 문서 수정 내용도 작업 보고서에 포함

## 버전 관리

프로젝트의 버전 관리는 Semantic Versioning (MAJOR.MINOR.PATCH) 를 기반으로 하며, 아래의 내부 규칙을 추가로 적용한다.

### 개발 단계 버전 정책

프로덕션 릴리즈 이전까지 MAJOR 버전은 0으로 유지한다.
0.x.y 구간에서는 하위 호환성 보장이 필수가 아니다.
개발 단계에서는 실험적 기능, 구조 변경, API 변경이 자유롭게 이루어질 수 있다.

### 프로덕션 단계 버전 정책

최초 프로덕션 배포 시 MAJOR 버전을 1로 올린다.
1.0.0부터는 하위 호환성을 명시적으로 관리한다.

### 버전 업 규칙

- MAJOR 버전 업 : Breaking Change가 발생한 경우
- MINOR 버전 업 : 기능 단위 변경
  - 신규 기능 추가
  - 기존 기능 확장
  - 새로운 API / 화면 / 옵션 추가
  - 사용자 행동이 추가되지만 기존 흐름은 유지되는 경우
- PATCH 버전 업 : 기능 변화 없는 수정
  - 버그 수정
  - 성능 개선
  - 내부 리팩터링
  - 로그, 예외 메시지 수정

### 프로젝트 별 버전

프로젝트 버전은 각 프로젝트별로 독립된 버전 체계를 사용한다.

**버전 위치**:
- `apps/web/package.json`
- `apps/core-api/build.gradle`
- `services/market-data/pyproject.toml`

### 문서 버전

문서 버전은 프로젝트 버전과 독립적이다.

**원칙**:
  
- 문서 상단에 `> 버전: v0.1.0` 형식으로 표기
- 개정 이력에 버전 변경 사항 기록

**적용 대상 문서**:
- docs/01_project_summary.md
- docs/02_core_architecture.md
- docs/03_marketdata_pipeline.md
- docs/04_ondemand_symbol_streaming.md
- docs/05_development_phases.md
- docs/06_db_schema.md
- docs/07_springboot_r2dbc.md

# git 작업 방식

## git commit 시 유의

- 작업할 내용들(git status 로 확인)을 같은 작업 단위로 쪼개서 커밋을 생성
- 커밋 제목, 커밋 내용, 커밋할 파일 목록을 만들어서 `stash/commit/` 경로에 `YYYYMMDD_to_commit.md` 파일을 작성 
- git commit 작업을 수행하는 과정에서 수행할 명령어를 보여주면서 커밋할 내역을 항상 사용자에게 승인받기고 commit 을 수행

## git push 금지

- push는 사용자가 직접 수행
- AI 에이전트는 절대 push 하지 말기

## git commit 메시지 양식

커밋 메시지는 다음 형식을 따라서 한글로 작성한다.

```
[타입] (범위) 간결한 설명

```

### 타입

- `[feat]`: 새로운 기능 추가
- `[fix]`: 버그 수정
- `[chore]`: 빌드, 설정, 의존성 등 기타 작업
- `[refactor]`: 코드 리팩토링
- `[docs]`: 문서 수정
- `[test]`: 테스트 코드

### 범위

- `(web)`: 프론트엔드 (apps/web)
- `(core-api)`: 백엔드 API (apps/core-api)
- `(market-data)`: 시세 수집 서비스 (services/market-data)
- `(ai-agent)`: AI 에이전트 서비스 (services/ai-agent)

### 설명

- 최대한 간결하게 개조식으로 작성
- 무엇을 했는지보다 목적과 기능 위주로 설명

### 커밋 예시

```
[feat] (web) 온보딩 UI 및 로그인 페이지 리팩토링

- 온보딩 관련 페이지(welcome, add, agree, check, survey 등) UI 및 레이아웃 개선
- 로그인 페이지 디자인 업데이트 및 백엔드 URL 상수 적용
- GlobalNavBar 컴포넌트 수정

```

```
[fix] (core-api) 회원가입 프로세스 IP 주소 추출 시 NPE 방지

- SignupController에서 remoteAddress.getAddress()가 null일 경우 발생하는 NullPointerException 수정
```

```
[feat] (market-data) active_symbols 키 계층화
    
- active_symbols redis key에 {provider} 키 계층 추가
- provider 별로 심볼을 따로 관리하기 위함
- 추후에는 provider 정보를 캐시 또는 클라이언트로부터 받는 방안을 고려
```

# 코딩 컨벤션

## 공통

- 코드는 읽기 쉽고 유지보수하기 쉽게 작성
- 변수명, 함수명은 명확하고 의미 있게 작성
- 주석은 코드로 설명이 어려운 부분에만 작성

## Java (core-api)

- Spring Boot 3.x 기반 WebFlux + R2DBC
- Entity는 `@Table` 어노테이션 사용
- Repository는 `R2dbcRepository` 상속
- Service 반환 타입은 `Mono<T>` 또는 `Flux<T>` 사용
- 관계 매핑은 R2DBC에서 지원하지 않으므로 수동 조인
- 자세한 내용은 [docs/07_springboot_r2dbc.md](docs/07_springboot_r2dbc.md) 참고

## TypeScript (web)

- Next.js 14+ App Router 사용
- React 함수형 컴포넌트 작성
- 상태 관리는 Zustand 사용
- TailwindCSS 기반 스타일링

## Python (market-data, ai-agent)

- Python 3.12+ 사용
- 비동기 처리는 asyncio 사용
- 타입 힌트 적극 활용
- 패키지 관리는 uv 사용

# 서비스 아키텍처

각 서비스의 구체적인 설계 원칙, 모듈 구조는 서비스별 문서 참고

## core-api

- **기능**: 백엔드 코어 비즈니스 로직, REST API, WebSocket 시세 중계
- **기술 스택**: Spring Boot 3.5.8 + WebFlux + R2DBC + PostgreSQL
- **디렉토리 위치**: `apps/core-api/`
- **관련 문서**: [docs/07_springboot_r2dbc.md](docs/07_springboot_r2dbc.md), [docs/02_core_architecture.md](docs/02_core_architecture.md)
- **실행 방법**:
  ```bash
  # Docker 인프라 실행
  docker compose up -d postgres redis

  # Docker 로 실행

  # 로컬 실행
  cd apps/core-api
  ./run-local.sh

  # Swagger UI
  open http://localhost:8080/swagger-ui.html
  ```
- **주요 기능**:
  - 사용자 인증/인가 (OAuth2, JWT)
  - 포트폴리오 CRUD 및 성과 지표 계산
  - Redis에서 현재가 조회 및 active_symbols 관리
  - AI 분석 요청

## web

- **기능**: 웹 애플리케이션 (UI/UX)
- **기술 스택**: Next.js 14+ + TypeScript + TailwindCSS + Zustand
- **디렉토리 위치**: `apps/web/`
- **관련 문서**: [docs/02_core_architecture.md](docs/02_core_architecture.md)
- **실행 방법**:
  ```bash
  cd apps/web
  npm run dev

  # 브라우저에서
  open http://localhost:3000
  ```
- **주요 기능**:
  - 대시보드 UI (히트맵, P&L, 포트폴리오 현황)
  - 온보딩 플로우 및 사용자 설정
  - core-api REST API 호출

## market-data

- **기능**: 실시간 시세 수집, 정규화, Redis 발행
- **기술 스택**: Python 3.12 + asyncio + Redis + WebSocket
- **디렉토리 위치**: `services/market-data/`
- **관련 문서**: [services/market-data/README.md](services/market-data/README.md), [docs/03_marketdata_pipeline.md](docs/03_marketdata_pipeline.md)
- **실행 방법**:
  ```bash
  cd services/market-data

  # uv 설치 (없을 경우)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Python 3.12 및 가상환경 설정
  uv venv --python 3.12
  source .venv/bin/activate
  uv sync

  # 예: 업비트 KRW-BTC 시세 수집
  uv run -m quote_pipeline.main --provider upbit --symbols KRW-BTC
  ```
- **주요 책임**:
- 시세 수신
  - 시세 데이터 정규화 및 Redis Pub/Sub (`quotes.tick`) 발행
  - Redis 캐시 (`quote:<symbol>`) 갱신
  - Provider별 active_symbols Set 기반 동적 구독 관리

## ai-agent

- **기능**: AI 기반 포트폴리오 분석 및 인사이트 생성 (예정)
- **기술 스택**: Python + FastAPI + LLM + Vector DB
- **디렉토리 위치**: `services/ai-agent/` (예정)
- **관련 문서**: [docs/02_core_architecture.md](docs/02_core_architecture.md), [docs/04_development_phases.md](docs/04_development_phases.md)
- **주요 책임**:
  - 분석 작업 수신
  - LLM 기반 포트폴리오/리스크 분석
  - 분석 결과를 PostgreSQL에 저장


