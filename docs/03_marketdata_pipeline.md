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