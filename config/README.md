# Redis 메타데이터 설정

이 디렉토리는 Port Rally 프로젝트의 중앙화된 Redis 메타데이터 스키마를 포함합니다.

## 파일

- **redis-meta.yml**: 모든 Redis 키 패턴, TTL, 메타데이터를 포함하는 메인 스키마 정의 파일
- **redis-meta.dev.yml**: (선택) 개발 환경 오버라이드

## 스키마 구조

### 서비스

스키마는 여러 서비스의 키를 정의합니다:

- **core-api** (Java): 인증 토큰 및 사용자 세션
- **market-data** (Python): 실시간 시세, 종목 메타데이터, 활성 종목

### 키 정의

각 키는 다음을 포함합니다:

- **pattern**: 파라미터가 포함된 템플릿 (예: `refresh_token:{token}`)
- **type**: Redis 데이터 타입 (value, hash, set, zset, list)
- **codec**: 데이터 인코딩 (string, json)
- **ttl**: 만료 시간 (밀리초 단위, null = 만료 없음)
- **description**: 목적 및 사용 방법 설명
- **params**: 타입 및 유효성 검증 규칙이 포함된 필수 파라미터
- **fields**: hash 타입의 경우, 예상되는 필드 목록

## 사용법

### Java (core-api)

키는 컴파일 타임에 annotation processor를 통해 생성됩니다:

```java
// 생성된 코드는 타입 안전한 빌더를 제공합니다
String key = RedisKeys.refreshToken(token).build();
String userKey = RedisKeys.userRefresh(userId).build();

// 메타데이터 접근
long ttl = RedisKeys.refreshToken(token).getTtl();
```

### Python (market-data)

키는 런타임에 Pydantic 유효성 검증과 함께 생성됩니다:

```python
from quote_pipeline.redis_meta import meta

# 런타임 유효성 검증과 함께 타입 안전
quote_key = meta.quote(
    national="KR",
    exchange="KOSPI",
    symbol="005930"
)

redis_key = quote_key.build()  # "quote:KR:KOSPI:005930"
ttl = quote_key.get_ttl()      # 60000 (1분)
```

### Python 타입 힌팅 (Stubs)

`quote_pipeline.redis_meta.meta` 객체는 런타임에 `redis-meta.yml`에서 Redis 키 정의를 동적으로 로드합니다. 이러한 동적 동작은 정적 분석 도구(IDE나 linter)가 동적으로 추가된 속성(`meta.quote`, `meta.active_symbols` 등)을 추론할 수 없기 때문에 오류("빨간 밑줄")를 보고할 수 있습니다.

이를 해결하기 위해 `services/market-data/src/quote_pipeline/redis_meta/`에 stub 파일(`__init__.pyi`)이 제공됩니다. 이 파일은 `meta` 객체의 예상되는 속성과 타입을 명시적으로 선언하여 정적 분석기가 코드를 올바르게 이해할 수 있도록 합니다.

**자동 생성 (권장):**
Stub 파일은 `redis-meta.yml`에서 자동으로 생성할 수 있습니다:

```bash
# 수동 생성
python scripts/generate_redis_stubs.py

# 검증 (CI/CD용)
python scripts/validate_redis_stubs.py
```

**Pre-commit Hook (선택):**
`.pre-commit-config.yaml`이 설정되어 있어 `redis-meta.yml` 변경 시 자동으로 stub 파일이 생성됩니다:

```bash
# pre-commit 설치 (최초 1회)
pip install pre-commit
pre-commit install

# 이후 redis-meta.yml 변경 시 커밋 전 자동 생성
git add config/redis-meta.yml
git commit  # 자동으로 stub 파일 생성 및 추가
```

## 수정 가이드라인

1. **새로운 키 추가**: `redis-meta.yml`의 적절한 서비스 하위에 항목 추가
2. **패턴 변경**: 패턴을 업데이트하고 버전 증가
3. **키 폐기**: 대체 방법이 포함된 마이그레이션 항목 추가
4. **유효성 검증**: 프로덕션 안전성을 위해 params에 적절한 regex 유효성 검증 보장

## 스키마 유효성 검증

스키마는 서비스 시작 시 유효성 검증됩니다. 유효하지 않은 스키마는 애플리케이션 시작을 방지합니다.

## 버전 호환성

서비스는 스키마 버전을 추적하고 시작 시 호환성을 검증합니다:

- **min_version**: 최소 호환 스키마 버전
- **max_version**: 최대 호환 스키마 버전

이를 통해 서비스가 Redis 키 일관성을 유지하면서 독립적으로 배포할 수 있습니다.

## 핫 리로드 (개발 환경)

개발 모드에서:

- **Java**: 스키마 변경 시 재빌드 필요 (./gradlew build)
- **Python**: redis-meta.yml 변경 시 자동으로 리로드
