# active_symbols 동적 구독 흐름 (Upbit 예시)

## 개요
- Redis Set(`active_symbols`)을 주기적으로 폴링해 심볼 변경사항을 감지하고, 인게스터에 반영한다.
- 변경 감지 후:  
    - 인게스터가 `apply_symbols`를 지원하면 세션을 유지한 채 추가/삭제만 적용  
    - 지원하지 않으면 태스크를 취소하고 새 인게스터를 생성해 재구독

## 주요 구성
### 1) `active_symbols.py`
- `main.py` -> `manage_dynamic_ingestor(settings, sink)`  
  - Redis 클라이언트 생성 → `active_symbols` 초기값 seed(SADD)  
  - `fetch_active_symbols`: SMEMBERS로 Set 조회  
  - `while` 루프에서 `poll_interval_s`마다 Set을 읽어 이전값과 비교  
  - 변경 발생 시:
    - ingestor 에(ex. kis.py, upbit.py ...) `apply_symbols`가 있으면 호출해 심볼만 증감
    - 없으면 기존 태스크 취소 → 새 인게스터 생성 후 `run_forever` 태스크 시작
  - 종료 시 태스크 취소 및 `active_set` 삭제

### 2) Upbit 인게스터 (`ingestors/upbit.py`)
- `build_subscription_payload`가 현재 `self.symbols`를 payload로 생성  
- 구독 요청 시 payload 예:  
  ```json
  [
    {"ticket": "port-rally-poc"},
    {"type": "ticker", "codes": ["KRW-BTC", "KRW-XRP"], "isOnlyRealtime": true}
  ]
  ```
- Upbit 인게스터는 `apply_symbols`를 따로 구현하지 않음 → 심볼 변경 시 태스크 재시작

### 3) 파이프라인 (`pipeline.py`)
- `settings.dynamic.enabled`가 True일 때 `manage_dynamic_ingestor`를 호출  
- 동적 모드가 아니면 단일 인게스터로 `run_forever`

## 실행 흐름 (로그 예시)
1. 초기 구독: `KRW-BTC` → payload에 BTC만 포함  
2. Redis `active_symbols`에 `KRW-XRP` 추가 → 폴링 시 변경 감지  
3. 기존 Upbit 태스크 취소 → 새 인게스터 생성 → payload에 `KRW-BTC, KRW-XRP`로 재구독  
4. 로그:
   - `Active symbols changed: {'KRW-BTC'} -> {'KRW-BTC', 'KRW-XRP'}`
   - `[upbit] connecting ... / subscribed with payload=... ['KRW-BTC', 'KRW-XRP']`

## 참고 설정
- `Settings.dynamic.active_set`: 기본 `active_symbols`  
- `Settings.dynamic.poll_interval_s`: 기본 5초  
- Redis URL/채널: `Settings.redis.*` (env/CLI로 override 가능)
