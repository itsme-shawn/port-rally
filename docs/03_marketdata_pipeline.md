# 3. 실시간 시세 파이프라인 모듈 (Market Data) 상세

## 시세 파이프라인 모듈 목표
외부(거래소,API,크롤링)에서 수집된 원시 시세 데이터를 정제, 가공하여 코어 서버(spring webflux) 에 실시간으로 분배하는 모듈

## 7단계 파이프라인 구조 (services/market-data/)

| 계층 번호 | 계층 명칭 | 주요 역할 | 기술/구성 요소 |
| :---: | :--- | :--- | :--- |
| **1** | **데이터 수집 (Data Ingestion)** | 외부 WebSocket/REST API로부터 **원시 데이터 (Raw Data)** 수신 및 검증. | Python, `websocket_consumer.py`, `rest_poller.py` |
| **2** | **메시지 큐 (Stabilization)** | 수집기와 가공기 사이의 데이터 유실 및 병목 현상 방지. 대량 데이터 버퍼링. | **Kafka** (또는 RabbitMQ) |
| **3** | **데이터 가공 (Data Processing)** | 데이터 정규화, 타임스탬프 표준화, **보조 지표 (MA, RSI)** 실시간 계산. | Python Processor, `indicator_calculator.py` |
| **4** | **데이터 저장 (Persistence)** | 장기 시계열 저장 및 최신 상태 캐싱. | **TimescaleDB** (장기), **Redis** (스냅샷/최신 상태) |
| **5** | **데이터 분배 (Distribution)** | 가공된 데이터를 실시간 채널에 발행. | **Redis Pub/Sub** |
| **6** | **전송 서버 (Fan-out)** | WebSocket을 통해 프론트엔드에 데이터 푸시. 클라이언트 연결 관리. | Spring WebFlux API (`QuoteStreamService`, `WebSocketHandler`) |
| **7** | **운영/모니터링** | 시스템 상태 감시, 지연(Lag) 모니터링, 알람 설정. | Prometheus & Grafana |

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