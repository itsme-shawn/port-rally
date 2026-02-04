# Redis 키 관리 패턴 개선 계획

## 문제 정의

### 현재 상황
- **market-data (Python)**: Redis 키 패턴이 하드코딩되어 있음
  - `quote:{national}:{exchange}:{symbol}` (quote_store.py:136)
  - `active_symbols:{provider}` (ingestor_manager.py)
  - 일부만 환경 변수로 설정 가능 (REDIS_CHANNEL, REDIS_KEY_PREFIX_SYMBOL_METADATA)

- **core-api (Java)**: 완전히 하드코딩된 상수 사용
  - `REFRESH_TOKEN_PREFIX = "refresh_token:"` (RefreshTokenService.java:20)
  - `USER_TOKEN_PREFIX = "user_refresh:"` (RefreshTokenService.java:21)
  - 환경 변수 설정 불가

- **문제점**:
  - 키 변경 시 여러 파일 수정 필요
  - 서비스 간 키 불일치 위험
  - 타이핑 실수 가능
  - MSA 배포 시 일관성 유지 어려움

### 목표
1. ✅ Redis 키 하드코딩 제거
2. ✅ 여러 MSA 간 키 정의 공유
3. ✅ 개발 환경에서 변경 감지 (파일 워칭)
4. ✅ MSA 독립 배포 지원
5. ✅ 타입 안정성 확보 (컴파일 타임 에러 감지)

## 솔루션 개요

**접근법: Shared YAML Configuration + Code Generation**

```
redis-meta.yml (단일 진실의 소스)
        ↓
   [코드 생성기]
   ↙          ↘
redis_meta.py  RedisMeta.java
   ↓              ↓
market-data   core-api
```

### 핵심 원칙
- **Single Source of Truth**: `config/redis/redis-meta.yml`에 모든 메타데이터(키/채널) 정의
- **Type-Safe Code Gen**: Python/Java 상수 자동 생성으로 타이핑 실수 방지
- **Git-Committed**: 생성된 코드는 git에 커밋하여 리뷰 가능
- **Environment Override**: 배포 환경별 환경 변수 오버라이드 지원
- **Language Agnostic**: 향후 ai-agent, web 등 다른 서비스 추가 용이

### 선택 이유
| 대안 | 장점 | 단점 | 결정 |
|-----|------|------|------|
| **YAML + 코드 생성** | 타입 안정성, 오프라인 동작, 단순함 | 빌드 단계 필요 | ✅ **채택** |
| 환경 변수만 사용 | 간단함 | 20+ 변수 관리 어려움, 타입 안정성 없음 | ❌ |
| Spring Cloud Config | 중앙화, 런타임 업데이트 | 무거운 인프라, Java 종속 | ❌ |
| Shared NPM/PyPI 패키지 | 버전 관리 | 크로스 언어 패키징 복잡 | ❌ |
| Redis 자체를 config store로 | 영리함 | 순환 의존성, 부트스트랩 문제 | ❌ |

## 프로젝트 구조

```
port-rally/
├── config/
│   └── redis/
│       ├── redis-meta.yml              # ⭐ Redis 관련 메타데이터 설정 파일
│       └── README.md                   # 사용법 문서
│
├── scripts/
│   ├── generate-redis-meta.sh          # 마스터 생성 스크립트
│   ├── watch-redis-meta.sh             # 개발용 파일 워처
│   └── generators/
│       ├── generate_python.py          # Python 코드 생성기
│       └── generate_java.py            # Java 코드 생성기
│
├── services/market-data/src/quote_pipeline/
│   └── redis_meta.py                   # ⭐ 생성된 Python 상수 (git 커밋)
│
└── apps/core-api/src/main/java/api/config/
    └── RedisMeta.java                  # ⭐ 생성된 Java 클래스 (git 커밋)
```

## redis-meta.yml 스키마

```yaml
version: "1.0"
last_updated: "2026-02-02"

# Redis 키 정의
keys:
  # Quote 데이터 (market-data → core-api, web)
  quotes:
    pattern: "quote:{national}:{exchange}:{symbol}"
    description: "실시간 시세 데이터 (Redis Hash)"
    data_type: "hash"
    ttl: null
    fields: [symbol, provider, national, exchange, price, timestamp, volume, open, high, low, change, change_rate]
    env_override: "REDIS_KEY_PREFIX_QUOTE"
    owner: "market-data"
    consumers: ["core-api", "web", "ai-agent"]

  # 심볼 메타데이터
  symbol_metadata:
    pattern: "symbol_metadata:{symbol}"
    description: "심볼 메타데이터 (assets_master에서 로드)"
    data_type: "string"  # JSON
    ttl: null
    env_override: "REDIS_KEY_PREFIX_SYMBOL_METADATA"
    owner: "market-data"
    consumers: ["market-data", "core-api"]

  # 활성 심볼 구독 목록
  active_symbols:
    pattern: "active_symbols:{provider}"
    description: "제공자별 활성 구독 심볼 (Set)"
    data_type: "set"
    ttl: null
    env_override: "ACTIVE_SYMBOL_SET"
    owner: "market-data"
    consumers: ["market-data", "core-api"]

  # 인증 토큰 (core-api 전용)
  auth:
    refresh_token:
      pattern: "refresh_token:{token}"
      description: "Refresh 토큰 → userId 매핑"
      data_type: "string"
      ttl: 604800  # 7일
      owner: "core-api"
      consumers: ["core-api"]

    user_refresh:
      pattern: "user_refresh:{userId}"
      description: "User → Refresh 토큰 매핑 (단일 세션)"
      data_type: "string"
      ttl: 604800  # 7일
      owner: "core-api"
      consumers: ["core-api"]

# Pub/Sub 채널
channels:
  quotes:
    name: "quotes"
    description: "실시간 시세 스트리밍 채널"
    env_override: "REDIS_CHANNEL"
    publisher: "market-data"
    subscribers: ["core-api", "web"]
```

## 구현 단계

### 1단계: 인프라 구축 (1일)

**생성 파일**:
- `config/redis/redis-meta.yml` - Redis 키 스키마 정의
- `config/redis/README.md` - 사용법 문서
- `scripts/generate-redis-meta.sh` - 마스터 생성 스크립트
- `scripts/watch-redis-meta.sh` - 파일 워처 (개발용, optional)

**작업**:
1. `config/redis/` 디렉토리 생성
2. 현재 사용 중인 모든 Redis 키를 `redis-meta.yml`에 정의
3. 검증: YAML 문법 확인 (`python -c "import yaml; yaml.safe_load(open('config/redis/redis-meta.yml'))"`)

### 2단계: Python 코드 생성기 구현 (1일)

**생성 파일**:
- `scripts/generators/generate_python.py`

**생성 대상**:
- `services/market-data/src/quote_pipeline/redis_meta.py`

**주요 기능**:
```python
class RedisMeta:
    @staticmethod
    def quote(national: str, exchange: str, symbol: str) -> str:
        """quote:US:NAS:NVDA"""
        prefix = os.getenv("REDIS_KEY_PREFIX_QUOTE", "quote")
        return f"{prefix}:{national}:{exchange}:{symbol}"

    @staticmethod
    def symbol_metadata(symbol: str) -> str:
        """symbol_metadata:NVDA"""
        prefix = os.getenv("REDIS_KEY_PREFIX_SYMBOL_METADATA", "symbol_metadata")
        return f"{prefix}:{symbol}"

    @staticmethod
    def active_symbols(provider: str) -> str:
        """active_symbols:kis"""
        prefix = os.getenv("ACTIVE_SYMBOL_SET", "active_symbols")
        return f"{prefix}:{provider}"

    @staticmethod
    def refresh_token(token: str) -> str:
        """refresh_token:{token}"""
        return f"refresh_token:{token}"

    @staticmethod
    def user_refresh(user_id: str) -> str:
        """user_refresh:{userId}"""
        return f"user_refresh:{user_id}"

    @staticmethod
    def channel_quotes() -> str:
        """quotes"""
        return os.getenv("REDIS_CHANNEL", "quotes")
```

**테스트**:
```bash
cd /workspaces/port-rally
python3 scripts/generators/generate_python.py
# 확인: services/market-data/src/quote_pipeline/redis_meta.py 생성됨
```

### 3단계: Java 코드 생성기 구현 (1일)

**생성 파일**:
- `scripts/generators/generate_java.py`

**생성 대상**:
- `apps/core-api/src/main/java/api/config/RedisMeta.java`

**주요 기능**:
```java
@Component
public class RedisMeta {
    private final Environment env;

    public RedisMeta(Environment env) {
        this.env = env;
    }

    public String quote(String national, String exchange, String symbol) {
        String prefix = env.getProperty("REDIS_KEY_PREFIX_QUOTE", "quote");
        return String.format("%s:%s:%s:%s", prefix, national, exchange, symbol);
    }

    public String refreshToken(String token) {
        return "refresh_token:" + token;
    }

    public String userRefresh(String userId) {
        return "user_refresh:" + userId;
    }

    public String channelQuotes() {
        return env.getProperty("REDIS_CHANNEL", "quotes");
    }
}
```

**테스트**:
```bash
python3 scripts/generators/generate_java.py
# 확인: apps/core-api/src/main/java/api/config/RedisMeta.java 생성됨
```

### 4단계: market-data 마이그레이션 (1-2일)

**수정 파일**:
- `services/market-data/src/quote_pipeline/stores/quote_store.py`
- `services/market-data/src/quote_pipeline/services/symbol_service.py`
- `services/market-data/src/quote_pipeline/ingestors/ingestor_manager.py`
- `services/market-data/src/quote_pipeline/publishers/redis_publisher.py`

**변경 예시 (quote_store.py)**:
```python
# Before
key = f"{self._key_prefix}:{national}:{exchange}:{symbol}"

# After
from quote_pipeline.redis_meta import redis_meta

key = redis_meta.quote(national, exchange, symbol)
```

**변경 예시 (ingestor_manager.py)**:
```python
# Before
provider_set = f"{self.settings.dynamic.active_set}:{provider.value}"

# After
from quote_pipeline.redis_meta import redis_meta

provider_set = redis_meta.active_symbols(provider.value)
```

**테스트**:
```bash
cd services/market-data
# 유닛 테스트
pytest tests/test_redis_meta.py

# 통합 테스트 (로컬 Redis 필요)
./run-market-data-local.sh
# Redis에서 키 확인
redis-cli KEYS "quote:*"
redis-cli SMEMBERS "active_symbols:kis"
```

### 5단계: core-api 마이그레이션 (1-2일)

**수정 파일**:
- `apps/core-api/src/main/java/api/service/auth/RefreshTokenService.java`

**변경 예시**:
```java
// Before
private static final String REFRESH_TOKEN_PREFIX = "refresh_token:";
private static final String USER_TOKEN_PREFIX = "user_refresh:";

// After
@Service
@RequiredArgsConstructor
public class RefreshTokenService {
    private final RedisMeta redisMeta;  // DI
    private final ReactiveRedisTemplate<String, String> redisTemplate;
    private final JwtConfig jwtConfig;

    public Mono<Void> saveRefreshToken(UUID userId, String refreshToken) {
        Duration ttl = Duration.ofMillis(jwtConfig.getRefreshTokenExpiration());
        String userIdStr = userId.toString();

        return redisTemplate.opsForValue()
            .get(redisMeta.userRefresh(userIdStr))  // ✅ 생성된 메서드 사용
            .flatMap(oldToken -> redisTemplate.delete(redisMeta.refreshToken(oldToken)))  // ✅
            .then(redisTemplate.opsForValue()
                .set(redisMeta.refreshToken(refreshToken), userIdStr, ttl))  // ✅
            .then(redisTemplate.opsForValue()
                .set(redisMeta.userRefresh(userIdStr), refreshToken, ttl));  // ✅
    }
}
```

**테스트**:
```bash
cd apps/core-api
# 유닛 테스트
./gradlew test --tests RefreshTokenServiceTest

# 통합 테스트
./run-core-api-local.sh
# 로그인 테스트 후 Redis 확인
redis-cli KEYS "refresh_token:*"
redis-cli KEYS "user_refresh:*"
```

### 6단계: 문서화 및 배포 (1일)

**문서 업데이트**:
- `README.md` - Redis 키 관리 섹션 추가
- `config/redis/README.md` - 상세 사용법
- `.env.example` - 새로운 환경 변수 예시

**환경 변수 추가 (.env.dev, .env.prod)**:
```bash
# Redis Key Overrides (optional)
# REDIS_KEY_PREFIX_QUOTE=quote
# REDIS_KEY_PREFIX_SYMBOL_METADATA=symbol_metadata
# ACTIVE_SYMBOL_SET=active_symbols
# REDIS_CHANNEL=quotes
```

**Git 커밋**:
```bash
git add config/redis/redis-meta.yml
git add scripts/generate-redis-meta.sh
git add scripts/generators/*.py
git add services/market-data/src/quote_pipeline/redis_meta.py
git add apps/core-api/src/main/java/api/config/RedisMeta.java
git add [마이그레이션된 파일들]
git commit -m "[refactor] Redis 키 관리 중앙화 (YAML + 코드 생성)"
```

## 검증 방법

### End-to-End 테스트

1. **market-data 시세 수집 확인**:
```bash
# 서비스 시작
docker compose -f docker-compose.dev.yml up -d market-data

# Redis 키 확인
redis-cli KEYS "quote:*"
# 예상: quote:US:NAS:NVDA, quote:CRYPTO:UPBIT:KRW-BTC, ...

redis-cli SMEMBERS "active_symbols:kis"
# 예상: NVDA, AAPL, ...

redis-cli SUBSCRIBE quotes
# 예상: 실시간 시세 메시지 수신
```

2. **core-api 인증 플로우 확인**:
```bash
# API 시작
docker compose -f docker-compose.dev.yml up -d core-api

# 로그인 테스트 (예: Google OAuth)
curl -X POST http://localhost:8080/api/v1/auth/login ...

# Redis 토큰 확인
redis-cli KEYS "refresh_token:*"
redis-cli KEYS "user_refresh:*"
```

3. **환경 변수 오버라이드 테스트**:
```bash
# .env.dev에 추가
REDIS_KEY_PREFIX_QUOTE=custom_quote

# 재시작
docker compose restart market-data

# 확인
redis-cli KEYS "custom_quote:*"
# 예상: custom_quote:US:NAS:NVDA
```

### 유닛 테스트

**Python (services/market-data/tests/test_redis_meta.py)**:
```python
import pytest
import os
from quote_pipeline.redis_meta import redis_meta

def test_quote_key_format():
    key = redis_meta.quote("US", "NAS", "NVDA")
    assert key == "quote:US:NAS:NVDA"

def test_symbol_metadata_with_env(monkeypatch):
    monkeypatch.setenv("REDIS_KEY_PREFIX_SYMBOL_METADATA", "custom_meta")
    key = redis_meta.symbol_metadata("AAPL")
    assert key == "custom_meta:AAPL"

def test_active_symbols():
    key = redis_meta.active_symbols("upbit")
    assert key == "active_symbols:upbit"
```

**Java (apps/core-api/src/test/java/api/config/RedisMetaTest.java)**:
```java
@SpringBootTest
class RedisMetaTest {
    @Autowired
    private RedisMeta redisMeta;

    @Test
    void testRefreshTokenKey() {
        String key = redisMeta.refreshToken("abc-123");
        assertEquals("refresh_token:abc-123", key);
    }

    @Test
    void testUserRefreshKey() {
        String key = redisMeta.userRefresh("user-456");
        assertEquals("user_refresh:user-456", key);
    }
}
```

## 개발 워크플로우

### 새 Redis 키 추가 시

1. `config/redis/redis-meta.yml` 편집:
```yaml
keys:
  portfolio_cache:
    pattern: "portfolio:{userId}"
    description: "사용자 포트폴리오 캐시"
    data_type: "hash"
    ttl: 3600
    owner: "core-api"
    consumers: ["core-api", "web"]
```

2. 코드 생성:
```bash
./scripts/generate-redis-meta.sh
```

3. 생성된 코드 확인:
```python
# redis_meta.py에 자동 추가됨
@staticmethod
def portfolio_cache(user_id: str) -> str:
    return f"portfolio:{user_id}"
```

4. 서비스에서 사용:
```python
from quote_pipeline.redis_meta import redis_meta

cache_key = redis_meta.portfolio_cache(user_id)
```

5. Git 커밋:
```bash
git add config/redis/redis-meta.yml
git add services/market-data/src/quote_pipeline/redis_meta.py
git add apps/core-api/src/main/java/api/config/RedisMeta.java
git commit -m "[feat] portfolio_cache Redis 키 추가"
```

### 개발 중 자동 재생성 (Optional)

```bash
# 터미널 1: 파일 워처 실행
./scripts/watch-redis-meta.sh

# 터미널 2: redis-meta.yml 편집
vim config/redis/redis-meta.yml

# 저장 시 자동으로 코드 재생성됨
```

## 향후 확장

### TypeScript 지원 (web에서 직접 Redis 접근 시)
```bash
# 생성기 추가
scripts/generators/generate_typescript.py

# 생성 대상
apps/web/src/lib/redisMeta.ts
```

### ai-agent 서비스 추가
```bash
# Python이므로 동일한 redis_meta.py 사용
services/ai-agent/src/redis_meta.py
```

### Validation 강화
```yaml
# config/redis/redis-meta.schema.json 추가
# JSON Schema로 YAML 구조 검증
```

## 트레이드오프 및 고려사항

### 장점
✅ 단일 진실의 소스로 일관성 보장
✅ 타입 안정성 (컴파일 타임 에러)
✅ IDE 자동완성 지원
✅ Git 히스토리로 변경 추적
✅ 코드 리뷰 가능
✅ 오프라인 동작 (외부 서비스 불필요)
✅ MSA 독립 배포 지원

### 단점 및 해결책
⚠️ 빌드 단계 추가
  → 해결: 사전에 생성하여 git 커밋 (빌드 시 생성 불필요)

⚠️ redis-meta.yml 변경 시 수동 재생성 필요
  → 해결: pre-commit hook 또는 watch 스크립트 제공

⚠️ 런타임 키 변경 불가
  → 해결: 환경 변수 오버라이드로 유연성 확보

## 핵심 파일 목록

### 새로 생성
1. `config/redis/redis-meta.yml` - ⭐ Redis 메타데이터(키/채널) 정의 (단일 진실의 소스)
2. `config/redis/README.md` - 사용법 문서
3. `scripts/generate-redis-meta.sh` - 마스터 생성 스크립트
4. `scripts/watch-redis-meta.sh` - 개발용 파일 워처
5. `scripts/generators/generate_python.py` - Python 코드 생성기
6. `scripts/generators/generate_java.py` - Java 코드 생성기
7. `services/market-data/src/quote_pipeline/redis_meta.py` - 생성된 Python 상수
8. `apps/core-api/src/main/java/api/config/RedisMeta.java` - 생성된 Java 클래스

### 수정 필요
9. `services/market-data/src/quote_pipeline/stores/quote_store.py` - quote 키 패턴 사용처
10. `services/market-data/src/quote_pipeline/services/symbol_service.py` - symbol_metadata 키 사용처
11. `services/market-data/src/quote_pipeline/ingestors/ingestor_manager.py` - active_symbols 키 사용처
12. `services/market-data/src/quote_pipeline/publishers/redis_publisher.py` - channel 사용처
13. `apps/core-api/src/main/java/api/service/auth/RefreshTokenService.java` - 토큰 키 상수 제거
14. `README.md` - Redis 메타데이터 관리 섹션 추가
15. `.env.example` - 환경 변수 예시 추가

## 타임라인

| 단계 | 작업 | 예상 소요 | 담당 |
|-----|-----|----------|-----|
| 1 | 인프라 구축 (YAML, 스크립트) | 1일 | Dev |
| 2 | Python 생성기 구현 | 1일 | Dev |
| 3 | Java 생성기 구현 | 1일 | Dev |
| 4 | market-data 마이그레이션 | 1-2일 | Dev |
| 5 | core-api 마이그레이션 | 1-2일 | Dev |
| 6 | 테스트 및 문서화 | 1일 | Dev |
| **합계** | | **6-8일** | |

## 성공 기준

✅ 모든 Redis 키와 채널이 `redis-meta.yml`에 정의됨
✅ 하드코딩된 키 문자열이 코드에서 제거됨
✅ 생성된 Python/Java 코드가 정상 작동
✅ 환경 변수 오버라이드 테스트 통과
✅ E2E 테스트 (시세 수집 → Redis 저장 → API 조회) 성공
✅ 인증 플로우 (로그인 → 토큰 저장 → 갱신) 성공
✅ 문서 업데이트 완료
