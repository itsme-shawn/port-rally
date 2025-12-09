# 3. 실시간 시세 파이프라인 모듈 (Market Data) 상세

## 시세 파이프라인 모듈 목표
외부(거래소,API,크롤링)에서 수집된 원시 시세 데이터를 정제, 가공하여 코어 서버(spring webflux) 에 실시간으로 분배하는 모듈

## 시세 흐름 개요

거래소 WS/Feed
→ Ingestor (active_symbols 기반으로 구독 종목 결정)
→ Redis pub/sub: `quotes.tick` (Normalize된 틱 이벤트 실시간 publish)
→ Redis Cache Update (Quote 현재가 갱신)
- `quote:<symbol>` (현재가 캐시)
→ API Server (REST /quotes, 포트폴리오/관심 API)
→ WS Gateway (클라이언트 WebSocket push)

## 🔑 Phase 0: 시세 PoC 중요성
* **최우선 검증 목표:** 업비트/바이낸스 WebSocket **연결 안정성 (99% 이상 유지)** 및 **지연 시간 (< 1초)** 달성 가능성.
* **PoC 실패 시 대안:** Mock 데이터로 MVP 진행, 유료 API 검토, 지연 데이터 사용, 프로젝트 피봇. (리스크 최우선 관리)

## 여러 종목(심볼)에 대한 subscribe/unsubscribe 처리 (동적 구독)

- **구독 관리자 (Subscription Manager) 추가**
  - 역할: 심볼별 구독 상태를 중앙에서 관리하고, 인바운드 요청(API)으로 구독/해제를 트리거.
  - 위치: market-data 서비스 내부의 별도 모듈 또는 프로세스.
  - 기능:
      - 심볼별 ref-count(요청 수) 유지 → 0이 되면 구독 해제.
      - 동일 심볼에 대한 중복 구독 방지.
      - 구독/해제 결과/에러를 API로 되돌려 줄 수 있는 상태 관리.
- **Ingestor 에서의 처리:**
  - 외부 데이터 수신을 하는 Upbit/Binance/KIS Ingestor가 Subscription Manager로부터 “추가/삭제” 명령을 받아 동적으로 subscribe/unsubscribe.
  - 기존 단일 run_forever 패턴에서 “구독 추가 요청 큐”를 수신하는 비동기 루프를 추가.
- **Core API→구독 명령 경로:**
  - Core API(Spring WebFlux)에서 심볼 추가/삭제 엔드포인트 제공 → market-data로 gRPC/REST/Redis/Kafka 중 하나로 커맨드 채널을 통해 전달 → 상태/오류 반환.
- **로드/확장:**
  - 심볼 수가 많으면 거래소별 연결 제한이 있을 수 있으니 심볼별로 커넥션 풀 분할(예: Upbit는 여러 WS
연결로 코드 리스트 나눔).
  - rate limit 시 백오프/REST fallback 워커 준비.
- **상태 모니터링:**
  - 활성 구독 수, 심볼 목록, 최근 에러, 재연결 횟수 등을 메트릭/헬스 엔드포인트로 노출.
  - 수집된 시세 스트림을 Redis Pub/Sub 또는 Kafka 토픽으로 퍼블리시 → Core API/Web(WebSocket)에서 소비/팬아웃.