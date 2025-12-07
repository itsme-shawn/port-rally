# PortRally Agents Brief

PortRally는 개인 투자자 대상 실시간 포트폴리오 관리·AI 인사이트 서비스를 목표로 합니다. 아래는 `docs/` 내용을 요약한 에이전트용 브리핑입니다.

## 1) 서비스 핵심 요약 (`docs/01_project_summary.md`)
- 대상: 초보~중급 개인 투자자.  
- 가치 제안: 실시간 대시보드(히트맵, P&L), AI 인사이트(위험도/상관관계, LLM 리포트, 리밸런싱 제안), 실시간 알림(가격·변동성·뉴스).  
- KPI: MAU, 연결 계좌 수, 알림 CTR, AI 추천 실행률, 리포트 구독 잔존율.  
- 리스크/준수: 실시간 시세 확보, 자산/주문 데이터 암호화 및 토큰 관리, 투자권유 금지 문구, XAI, 로그 보관.

## 2) 시스템 아키텍처 & 스택 (`docs/02_core_architecture.md`)
- 구조: 모노레포 + MSA 지향, Reactive 중심.  
- 주요 경로: `apps/api`(Spring WebFlux BFF), `apps/web`(Next.js/Tailwind/Zustand), `services/market-data`(Python + Kafka/Timescale/Redis), `services/agent`(Python FastAPI + LLM/RAG), `packages`, `infrastructure`.  
- 데이터/캐시: Postgres(RDB), TimescaleDB(시계열), Redis(세션·스냅샷·Pub/Sub).  
- 메시징: Kafka(or Redis Streams)로 버퍼링, Redis Pub/Sub로 실시간 분배.  
- API 서버: WebFlux로 REST/WebSocket, `PortfolioService`, `QuoteStreamService`, `InsightService`, `NewsService`, `AlertService`.

## 3) 시세 파이프라인 (`docs/03_marketdata_pipeline.md`)
- 목표: 외부 WS/REST 시세 → 정제/지표 계산 → Redis Pub/Sub → WebSocket 팬아웃.  
- 7단계: 1)수집(WS/REST) 2)큐(Kafka) 3)가공/지표 4)저장(Timescale/Redis) 5)분배(Redis Pub/Sub) 6)전송(WebFlux WS) 7)모니터링(Prom/Grafana).  
- P0 PoC 기준: 업비트/바이낸스 WS 안정성 99%+, 지연 <1s. 실패 시 Mock/유료 API/지연 데이터로 피벗.

## 4) 개발 단계 & 크리티컬 패스 (`docs/04_development_phases.md`)
- 총 17주 예상(여유 포함 5~6개월).  
- Phase 핵심:  
  - P0(1.5주): 시세 PoC, 간단 Redis 저장 (`services/market-data`).  
  - P1(2주): JWT 인증/인가, 포트폴리오·포지션 CRUD, WebFlux 기본 (`apps/api`).  
  - P2(1.5주): Kafka/Timescale/Redis Pub/Sub 연동, 지표 계산.  
  - P3(2주): 웹 대시보드 + WebSocket 실시간 P/L/히트맵 (`apps/web`).  
  - P4(2주): AI 에이전트 서비스 기반(FastAPI, LLM, 벡터 DB) (`services/agent`).  
  - P5(2주): AI 인사이트 완성(리스크, 상관관계, LLM 리포트, 리밸런싱) (`services/agent`).  
- Nice-to-have: 알림 엔진, 뉴스 기능, 모바일 앱(RN/Flutter), 이미지 인식.  
- 팁/리스크: P0 결과로 Go/No-Go 판단, 이후 병렬화 가능; Prometheus/Grafana 모니터링 조기 도입.

## 5) 준수/운영 체크리스트
- 실시간 시세 공급 안정성 모니터링, 지연 및 데이터 유실 대응.  
- 개인정보/자산 데이터 암호화, 액세스 토큰 보안 저장(Vault/SM), 로그/감사 추적.  
- 투자권유 금지 문구 삽입 및 설명가능성 확보(XAI), 보관 정책 준수.  
- WebSocket 연결 관리 및 오류 시 재연결 전략 확보.

## 6) 테스트(시세 모듈) 메모
- 도구: `pytest`, `pytest-asyncio`, mock/fakeredis 기반 단위 테스트 계획.  
- 대상: 유틸(`trading_hours` 시장/장시간 판단), Sink 직렬화/호출, Ingestor(Upbit/Binance/KIS) 메시지→Sink 전달, Pipeline의 provider별 선택/설정 반영.  
- 구조 제안: `services/market-data/tests/` 아래 `test_trading_hours.py`, `test_stdout_sink.py`, `test_pipeline.py` 등 테스트 대상 소스 파일명 매칭 방식.  
- 실행: `uv run -m pytest services/market-data/tests` (env: 필요한 경우 KIS 자격/Redis URL 설정).
