# 4. 개발 단계 (Phase) 및 MVP 태스크

## 예상 타임라인
총 약 **17주** (4개월), 주말/여유 포함 시 5-6개월 예상.

## Critical Path (MVP 달성 필수)

| Phase | 기간 | 목표 및 핵심 태스크 | 담당 모듈 |
| :--- | :--- | :--- | :--- |
| **P0** | 1.5주 | **시세 PoC (최우선):** WebSocket 연결 안정성 검증, 간단한 Redis 저장. | `services/market-data/` |
| **P1** | 2주 | **코어 API 기반 구축:** JWT 인증/인가, 포트폴리오/포지션 CRUD (수동 입력), Spring WebFlux 설정. | `apps/api/` |
| **P2** | 1.5주 | **시세 파이프라인 완성:** Kafka, TimescaleDB, Redis Pub/Sub 연동, 지표 계산. | `services/market-data/` |
| **P3** | 2주 | **웹 대시보드 구현:** 포트폴리오 입력 화면, 실시간 P/L, 히트맵, **WebSocket 연동** (`useWebSocket`). | `apps/web/` |
| **P4** | 2주 | **AI 에이전트 서비스 기반:** FastAPI 서버, LLM 클라이언트, 벡터 DB (RAG) 설정. | `services/agent/` |
| **P5** | 2주 | **AI 인사이트 기능:** 리스크 점수, 상관관계 분석, **LLM 기반 자연어 리포트** 및 리밸런싱 제안. | `services/agent/` |

## Nice to Have (MVP 이후 고려)
* **P6 (1주):** 알림 시스템 (가격/변동성/뉴스 알림 규칙 엔진, WebSocket 푸시).
* **P7 (1주):** 뉴스 기능 (RSS 크롤러, 종목별 뉴스 피드, 감성 점수).
* **모바일 앱:** React Native/Flutter 기반 개발. (RN이 React/Next 기반과 기술 스택 통일성 측면에서 유리.)
* **이미지 인식:** 자산 입력의 정확도 및 편리성 향상.

## 🔑 개발 팁 및 리스크 관리
* **리스크 우선 검증:** Phase 0의 시세 파이프라인이 가장 불확실하며, 1.5주 내 Go/No-Go 결정 후 대안 전략 수립.
* **병렬 작업:** P1 완료 후, 코어 API와 웹 개발, 시세 파이프라인 완성, AI 에이전트 서비스 개발은 독립적으로 병렬 진행 가능.
* **모니터링:** 초기부터 Prometheus + Grafana 로깅 및 메트릭 설정하여 시스템 신뢰성 확보.