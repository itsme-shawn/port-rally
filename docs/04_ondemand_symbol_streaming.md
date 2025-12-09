# 온디맨드 방식의 시세 스트리밍 구독 가이드

## 1. 핵심 개념

* 시세 스트리밍은 **온디맨드 방식**으로 수행된다.
  * 즉, 전체 종목의 시세를 처음부터 스트리밍하는게 아니라, **사용자가 어떤 종목을 조회하거나 관심을 가진 시점에** 최초 REST 로 조회 이후, 해당 종목은 websocket 구독 대상으로 승격된다.
* 구독 대상은 Redis의 active_symbols Set으로 관리된다.
* active_symbols는 “동적이며 TTL 기반으로 유지되는 집합”이다.

---

## 2. 전체 아키텍처 개요

거래소 WS/Feed
→ Ingestor Service (active_symbols 기반으로 구독 종목 결정)
→ Redis pub/sub: `quotes.tick` (Normalize된 틱 이벤트 실시간 브로드캐스트)
→ Quote Cache Updater
→ Redis
- `quote:<symbol>` (현재가 캐시)
- active_symbols (구독 대상 종목 Set)
→ API Server (REST /quotes, 포트폴리오/관심 API)
→ WS Gateway (클라이언트 WebSocket push)

모든 구성 요소는 “종목(symbol) 기준 단일 상태 관리” 원칙을 따른다.

---

## 3. 핵심 데이터 모델

공통 이벤트 포맷
symbol: 종목 코드
price: 시세
ts_exchange: 거래소 시각
ts_ingested: 인입 시각

예:
{ "provider": "upbit", "symbol": "KRW-BTC", "price": 12345678.9, "ts_exchange": 17338..., "ts_ingested": 17338... }

---

## 4. 구독 대상 관리: active_symbols

active_symbols는 Redis의 Set 구조이며, 실시간 구독 대상 종목을 의미한다.
active_symbols는 사용자별 Set 이 아닌 시스템 전체에 해당하는 Set 이다.

### active_symbols에 추가되는 경우

1. 종목 검색: 검색된 종목은 TTL이 설정된 구독 종목으로 추가된다.

   * 이유: 검색 직후 시세가 변하는 모습을 실시간으로 보여주기 위함
   * cold start 방지: 검색 후 바로 실시간 데이터가 흐르도록 만들기 위한 장치
   * TTL 예: 5분~10분

2. 관심종목 추가: TTL이 설정된 구독 종목으로 추가된다.

3. 사용자 포트폴리오 편입: TTL이 설정된 구독 종목으로 추가된다.

4. (향후) 인기종목/최근검색 TOP N 등 추가 정책 가능

### active_symbols 정리/초기화 정책

active_symbols는 시간이 지날수록 커지므로 정기적 관리가 필요하다.

1. Ingestor 시작 시 초기화

   * 관심/포트폴리오 기반 영구 구독 심볼만 다시 로드
   * 검색 기반 임시 구독 심볼은 TTL 여부에 따라 자동 정리됨

2. TTL 기반 자동 정리
   * TTL 만료 시 active_symbols에서 제거

3. 배포 시 또는 주기적 Job에서 유지보수

   * 필요 시 active_symbols를 리셋하고 재구성

### 이 방식을 쓰는 이유 (효용성 및 cold start 해결)

* 검색된 종목도 실시간 시세가 즉시 반영됨 → UX 향상
* 검색 직후 시세가 멈춰있는 문제(cold start)를 근본적으로 차단
* 전체 종목을 풀로 구독하지 않으면서도 “사용자 관심 기반 최소 구독” 유지
* TTL 기반 구독을 통해 시스템 부하 최소화
* 관여도가 높은 종목 위주로 자연스러운 active_symbols 세트가 만들어짐

---

## 5. 시나리오별 동작 플로우

### (1) 종목 검색

사용자가 특정 종목을 검색한 경우:

1. API Server는 Redis `quote:<symbol>` 조회
2. 없으면 REST로 현재가 1회 조회
3. active_symbols에 TTL 기반으로 구독 대상으로 추가
4. Ingestor가 곧 해당 종목 구독을 시작하여 실시간 스트림이 흘러들어옴

---

### (2) 관심종목 추가 / 포트폴리오 편입

1. API Server는 DB에 저장
2. Redis SADD active_symbols <symbol> (TTL 없음 / 영구 구독)
3. Ingestor는 다음 폴링 시점에 구독 목록 변경 감지
4. 실시간 스트리밍이 즉시 활성화됨

---

### (3) WebSocket 구독

1. 클라이언트가 WS Gateway(core-api 내부 모듈)에 연결
2. subscribe 메시지로 특정 심볼들을 요청
3. WS Gateway는 세션별 구독 리스트에 등록
4. Redis pub/sub 의 "quotes.tick" 메시지 수신
5. 해당 symbol을 구독한 세션에게만 push

---

## 6. 에러/예외 처리

* quote:<symbol> 부재 + 외부 REST 실패 → API는 price=null, status="unavailable" 반환
* Ingestor 재시작 → active_symbols 기반 재구독 자동 복구
* Redis pub/sub 연결 문제 발생 시 자동 재접속 및 백오프
* TTL 기반 임시 구독 심볼은 만료 후 자동 정리됨

---

## 7. 전체 요약

* 시세 스트리밍은 “필요한 종목만 즉시 구독하는 온디맨드 방식”.
* active_symbols에 없는 종목은 최초 REST 로 조회하여 cold start 없이 실시간 대응 가능.
* active_symbols는 시스템이 처리해야 할 최소 시세 범위를 정의한다.
* 나중에 Kafka 로 변경하더라도 이 아키텍쳐를 확장할 수 있다.

---
