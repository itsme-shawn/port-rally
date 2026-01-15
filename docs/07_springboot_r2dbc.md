# Spring Boot Core API (R2DBC)

> 버전: v0.2.0
> 최종 수정일: 2026-01-15
> 프로젝트: apps/core-api
> 기술 스택: Spring Boot 3.5.8 + WebFlux + R2DBC + Flyway

## 개정 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-15 | v0.2.0 | 최신 코드 구조 반영 (Terms 도메인, V13 마이그레이션, Kafka/JWT 의존성 추가) |
| 2026-01-04 | v0.1.0 | JPA → R2DBC 전환 완료, V8 마이그레이션(Enum 변환) 반영 |
| 2025-Q4 | v0.0.0 | 초기 작성 (JPA 기반) |

---

## 목차

1. [개요](#1-개요)
2. [기술 스택](#2-기술-스택)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [구현 현황](#4-구현-현황)
5. [실행 가이드](#5-실행-가이드)
6. [개발 가이드](#6-개발-가이드)
7. [TODO](#7-todo)
8. [히스토리](#8-히스토리)

---

## 1. 개요

### 1.1 목적

Port Rally의 Core API는 투자 포트폴리오 관리 및 AI 분석 서비스를 제공하는 백엔드 서버다.

### 1.2 핵심 기능

- **사용자 관리**: OAuth2 소셜 로그인, 계정 관리, 약관 동의
- **포트폴리오**: 다중 포트폴리오, 종목 보유 현황, 성과 지표
- **AI 분석**: 포트폴리오/종목별 AI 인사이트
- **OCR**: 계좌 이미지 업로드 및 자동 종목 인식
- **알림**: 실시간 알림 발송 및 관리
- **약관**: 서비스 약관 관리 및 동의 이력

### 1.3 아키텍처

```
┌─────────────────────────────────────────────┐
│          Client (Web/Mobile)                │
└─────────────────┬───────────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────────┐
│         Spring Boot WebFlux                 │
│  ┌──────────────────────────────────────┐   │
│  │ Controller (REST API)                │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │ Service (비즈니스 로직)               │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │ R2DBC Repository (Reactive DB)       │   │
│  └──────────────┬───────────────────────┘   │
└─────────────────┼───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         PostgreSQL 16                       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         Redis (시세 캐시, Pub/Sub)           │
└─────────────────────────────────────────────┘
```

---

## 2. 기술 스택

### 2.1 Core

| 항목 | 기술 | 버전 |
|------|------|------|
| **Framework** | Spring Boot | 3.5.8 |
| **Language** | Java | 21 |
| **Build** | Gradle | 8.11.1 |
| **Database** | PostgreSQL | 16 |
| **ORM** | Spring Data R2DBC | 3.5.8 |
| **Migration** | Flyway | 10.23.0 |
| **Cache** | Redis | - |

### 2.2 Libraries

| 항목 | 라이브러리 | 용도 |
|------|----------|------|
| **Reactive** | Spring WebFlux | 비동기 웹 프레임워크 |
| **Security** | Spring Security | 인증/인가 |
| **Auth** | JJWT (io.jsonwebtoken) | JWT 토큰 생성 및 검증 |
| **Messaging** | Spring Kafka | 이벤트 기반 처리 (AI Agent 연동 등) |
| **Validation** | Hibernate Validator | 입력 검증 |
| **API Docs** | SpringDoc OpenAPI | Swagger UI |
| **Monitoring** | Spring Actuator | Health Check |

### 2.3 선택 이유

#### Spring WebFlux + R2DBC

**배경**:
- 실시간 시세 연동 시 비동기 처리 필요
- Market Data 서비스와의 통합 (Redis Pub/Sub)
- Thread per Request 모델의 확장성 한계

**장점**:
- Non-blocking I/O로 높은 동시성 처리
- 적은 스레드로 더 많은 요청 처리
- WebSocket 지원 (실시간 시세 전송)

**단점** (알고 있는 Trade-off):
- 러닝 커브가 높다
- 디버깅이 어렵다 (stacktrace 복잡)
- JPA 대비 기능 제한 (관계 매핑 미지원)

---

## 3. 프로젝트 구조

```
apps/core-api/
├── build.gradle
├── run-local.sh
└── src/main/
    ├── java/api/
    │   ├── CoreApiApplication.java
    │   │
    │   ├── config/                        # 설정 클래스
    │   │   ├── R2dbcConfig.java          # R2DBC Auditing, Repository 스캔
    │   │   ├── SecurityConfig.java        # Spring Security WebFlux
    │   │   └── GlobalExceptionHandler.java # 전역 예외 처리
    │   │
    │   ├── controller/                    # REST API 엔드포인트
    │   │   ├── UserController.java
    │   │   └── ...
    │   │
    │   ├── service/                       # 비즈니스 로직
    │   │   ├── user/
    │   │   └── ...
    │   │
    │   ├── dto/                           # 요청/응답 DTO
    │   │   ├── user/
    │   │   └── ...
    │   │
    │   ├── domain/                        # Entity
    │   │   ├── user/
    │   │   │   ├── User.java
    │   │   │   ├── SocialAccount.java
    │   │   │   └── UserPreference.java
    │   │   ├── portfolio/
    │   │   │   ├── Portfolio.java
    │   │   │   ├── Position.java
    │   │   │   ├── PortfolioMetric.java
    │   │   │   └── PortfolioAiInsight.java
    │   │   ├── asset/
    │   │   │   ├── Asset.java
    │   │   │   ├── AssetMetric.java
    │   │   │   └── AssetAiInsight.java
    │   │   ├── ocr/
    │   │   │   ├── UploadedImage.java
    │   │   │   ├── OcrResult.java
    │   │   │   └── OcrDetectedPosition.java
    │   │   ├── news/
    │   │   │   ├── NewsArticle.java
    │   │   │   └── NewsAssetRelation.java
    │   │   ├── notification/
    │   │   │   ├── NotificationType.java
    │   │   │   ├── UserNotificationSetting.java
    │   │   │   └── NotificationLog.java
    │   │   ├── audit/
    │   │   │   └── AuditLog.java
    │   │   └── terms/                     # Terms Domain
    │   │       ├── Terms.java
    │   │       └── UserTermsAgreement.java
    │   │
    │   ├── enums/                         # Enum
    │   │   └── ...
    │   │
    │   ├── exception/                     # Custom Exceptions
    │   ├── filter/                        # WebFilters (JWT, Logging etc.)
    │   ├── security/                      # Security Components (JWT Util etc.)
    │   │
    │   └── repository/                    # R2DBC Repository
    │       ├── user/
    │       ├── portfolio/
    │       ├── asset/
    │       ├── ocr/
    │       ├── news/
    │       ├── notification/
    │       ├── audit/
    │       └── terms/
    │
    └── resources/
        ├── application.yml                # 공통 설정
        ├── application-local.yml          # 로컬 환경
        └── db/migration/                  # Flyway 마이그레이션
            ├── R__01_Seed_Terms.sql
            ├── V1__create_user_tables.sql
            ├── V2__create_asset_tables.sql
            ├── V3__create_portfolio_tables.sql
            ├── V4__create_ocr_tables.sql
            ├── V5__create_news_tables.sql
            ├── V6__create_notification_tables.sql
            ├── V7__create_audit_tables.sql
            ├── V8__convert_enums_to_varchar.sql
            ├── V9__create_terms_tables.sql
            ├── V10__modify_unique_constraints_for_reregistration.sql
            ├── V11__add_fields_to_positions.sql
            ├── V12__add_fields_to_ocr_positions.sql
            └── V13__add_unique_constraint_to_positions.sql
```

---

## 4. 구현 현황

### 4.1 설정 파일

| 파일 | 상태 | 설명 |
|------|------|------|
| `build.gradle` | ✅ 완료 | Flyway, R2DBC, Redis, Security, JWT, Kafka 의존성 |
| `application.yml` | ✅ 완료 | R2DBC, Flyway, Redis, SpringDoc 설정 |
| `application-local.yml` | ✅ 완료 | 로컬 개발 환경 설정 |

### 4.2 Config 클래스

| 파일 | 상태 | 설명 |
|------|------|------|
| `R2dbcConfig.java` | ✅ 완료 | R2DBC Auditing, Repository 스캔 |
| `SecurityConfig.java` | ✅ 완료 | Spring Security WebFlux 설정 |
| `GlobalExceptionHandler.java` | ✅ 완료 | 전역 예외 처리 |

### 4.3 Flyway 마이그레이션

| 파일 | 테이블/내용 | 상태 |
|------|--------|------|
| `V1`~`V7` | User, Asset, Portfolio, OCR, News, Noti, Audit 테이블 생성 | ✅ |
| `V8` | PostgreSQL ENUM → VARCHAR 변환 | ✅ |
| `V9` | terms, user_terms_agreements 테이블 생성 | ✅ |
| `V10` | User/Social 재가입을 위한 Unique 제약조건 수정 | ✅ |
| `V11` | positions 테이블 컬럼 추가 (currency, broker 등) | ✅ |
| `V12` | ocr_detected_positions 테이블 컬럼 추가 | ✅ |
| `V13` | positions 중복 방지 제약조건 추가 | ✅ |
| `R__01` | 약관 데이터 시딩 (Repeatable) | ✅ |

### 4.4 도메인 계층

| 구분 | 개수 | 상태 |
|------|------|------|
| Enum | 13개 | ✅ 완료 |
| Entity | 19개 | ✅ 완료 (Terms 포함) |
| Repository | 18개 | ✅ 완료 (Terms 포함) |

### 4.5 User API (MVP)

| 파일 | 상태 |
|------|------|
| `UserController.java` | ✅ 완료 |
| `UserService.java` | ✅ 완료 |
| `CreateUserRequest.java` | ✅ 완료 |
| `UserResponse.java` | ✅ 완료 |

---

## 5. 실행 가이드

### 5.1 Docker 환경

```bash
# 전체 실행
docker compose up -d postgres redis
docker compose up --build core-api

# 로그 확인
docker compose logs -f core-api
```

### 5.2 로컬 개발

```bash
# 1. Docker 인프라 실행
docker compose up -d postgres redis

# 2. 애플리케이션 실행
cd apps/core-api
./run-local.sh

# 또는 Gradle 직접 실행
DB_HOST=localhost ./gradlew bootRun --args='--spring.profiles.active=local'
```

### 5.3 API 테스트

```bash
# Health Check
curl http://localhost:8080/actuator/health

# Swagger UI
open http://localhost:8080/swagger-ui.html

# User API 테스트
curl -X POST http://localhost:8080/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"displayName":"테스트","primaryEmail":"test@example.com"}'
```

### 5.4 PostgreSQL 접속

```bash
# Docker 컨테이너 접속
docker exec -it port-rally-postgres-1 psql -U postgres -d port_rally

# 테이블 목록 확인
\dt

# 특정 테이블 구조 확인
\d users

# 데이터 조회
SELECT * FROM users;

# 나가기
\q
```

---

## 6. 개발 가이드

### 6.1 JPA vs R2DBC 주요 차이점

| 항목 | JPA | R2DBC |
|------|-----|-------|
| **관계 매핑** | `@OneToMany` 지원 | 지원 안 함 (수동 조인) |
| **지연 로딩** | `FetchType.LAZY` | 없음 |
| **ID 생성** | `@GeneratedValue` | DB 기본값 사용 |
| **반환 타입** | Entity | `Mono<Entity>`, `Flux<Entity>` |
| **트랜잭션** | `@Transactional` | `@Transactional` (동일) |

### 6.2 Entity 작성 예시

```java
@Table("users")
public class User {
    @Id
    private UUID userId;  // DB에서 gen_random_uuid() 사용
    private UserStatus status;
    private String displayName;
    private String primaryEmail;
    private Boolean primaryEmailVerified;
    private Instant createdAt;
    private Instant updatedAt;
    private Instant deletedAt;  // Soft Delete

    // Getters/Setters (Lombok 사용 권장)
}
```

### 6.3 Repository 작성 예시

```java
@Repository
public interface UserRepository extends R2dbcRepository<User, UUID> {

    // 단순 조회
    Mono<User> findByPrimaryEmail(String email);

    // Soft Delete 고려
    @Query("SELECT * FROM users WHERE user_id = :userId AND deleted_at IS NULL")
    Mono<User> findActiveUser(@Param("userId") UUID userId);

    // 여러 건 조회
    Flux<User> findAllByStatusAndDeletedAtIsNull(UserStatus status);

    // 존재 확인
    Mono<Boolean> existsByPrimaryEmailAndDeletedAtIsNull(String email);
}
```

### 6.4 Service 작성 예시

```java
@Service
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional
    public Mono<User> createUser(CreateUserRequest request) {
        // 1. 중복 체크
        return userRepository.existsByPrimaryEmailAndDeletedAtIsNull(request.getEmail())
            .flatMap(exists -> {
                if (exists) {
                    return Mono.error(new BusinessException("Email already exists"));
                }

                // 2. Entity 생성
                User user = new User();
                user.setDisplayName(request.getDisplayName());
                user.setPrimaryEmail(request.getEmail());
                user.setStatus(UserStatus.PENDING);

                // 3. 저장
                return userRepository.save(user);
            });
    }

    public Mono<User> findById(UUID userId) {
        return userRepository.findById(userId)
            .switchIfEmpty(Mono.error(new NotFoundException("User not found")));
    }
}
```

### 6.5 Controller 작성 예시

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping
    public Mono<UserResponse> createUser(@Valid @RequestBody CreateUserRequest request) {
        return userService.createUser(request)
            .map(UserResponse::from);
    }

    @GetMapping("/{userId}")
    public Mono<UserResponse> getUser(@PathVariable UUID userId) {
        return userService.findById(userId)
            .map(UserResponse::from);
    }
}
```

### 6.6 ENUM 처리

V8 마이그레이션에서 PostgreSQL ENUM → VARCHAR로 변환 완료.
Java Enum은 String으로 자동 변환된다.

```java
// Enum 정의
public enum UserStatus {
    PENDING,
    ACTIVE,
    SUSPENDED,
    DELETED
}

// Entity에서 사용
@Table("users")
public class User {
    private UserStatus status;  // DB에서 VARCHAR로 저장/조회
}
```

### 6.7 Soft Delete 패턴

```java
// Entity
@Table("users")
public class User {
    private Instant deletedAt;

    public void softDelete() {
        this.deletedAt = Instant.now();
    }

    public boolean isDeleted() {
        return deletedAt != null;
    }
}

// Repository
@Repository
public interface UserRepository extends R2dbcRepository<User, UUID> {

    // 활성 사용자만 조회
    @Query("SELECT * FROM users WHERE deleted_at IS NULL")
    Flux<User> findAllActive();

    // Soft Delete 수행
    @Modifying
    @Query("UPDATE users SET deleted_at = NOW() WHERE user_id = :userId")
    Mono<Void> softDelete(@Param("userId") UUID userId);
}
```

---

## 7. TODO

### P0 - 필수

- [ ] 테스트 환경 설정 (`application-test.yml`, Testcontainers)
- [ ] 통합 테스트 작성 (User API)

### P1 - 핵심 기능

- [ ] Service 계층 확장 (Portfolio, Asset, Notification)
- [ ] Controller 계층 확장
- [ ] DTO 클래스 확장
- [ ] 입력 검증 강화 (Validator)

### P2 - 통합 기능

- [ ] OAuth2 인증 (Google, Kakao, Naver, Apple)
- [ ] JWT 토큰 발급/검증
- [ ] Redis 연동 (현재가 캐시, Pub/Sub)
- [ ] WebSocket 실시간 시세 전송

### P3 - 부가 기능

- [ ] 모니터링 (Actuator, Micrometer)
- [ ] Kafka 연동 (AI Agent 작업)
- [ ] S3 연동 (이미지 업로드)
- [ ] OCR 서비스 연동

---

## 8. 히스토리

### 8.1 JPA → R2DBC 전환 (2026-01-03)

#### 변경 이유

**당시 상황 (2024-Q4)**:
- Spring Data JPA 기반으로 초기 설계 완료
- `@OneToMany`, `@ManyToOne` 관계 매핑 사용
- 동기 blocking I/O로 인한 성능 우려

**고민한 부분**:
- JPA의 편리한 관계 매핑 vs R2DBC의 성능
- 러닝 커브 vs 확장성
- 기존 코드 재작성 비용

**결정 요인**:
1. **실시간 시세 연동**: Market Data 서비스와의 비동기 통합 필요
2. **확장성**: 트래픽 증가 시 Non-blocking I/O 필요
3. **일관성**: Market Data (Python asyncio) + Core API (Spring WebFlux) = 완전한 비동기 스택

**변경 작업 (2026-01-03)**:
- Entity 클래스에서 관계 매핑 제거
- Repository를 `R2dbcRepository`로 변경
- Service 반환 타입을 `Mono`/`Flux`로 변경
- Flyway V8 마이그레이션으로 ENUM → VARCHAR 변환

#### 주요 변경사항

**Entity 변환**:
```java
// Before (JPA)
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID userId;

    @OneToMany(mappedBy = "user")
    private List<Portfolio> portfolios;  // 관계 매핑
}

// After (R2DBC)
@Table("users")
public class User {
    @Id
    private UUID userId;  // DB에서 gen_random_uuid() 사용
    // portfolios는 제거, Repository에서 수동 조인
}
```

**Repository 변환**:
```java
// Before (JPA)
public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByPrimaryEmail(String email);
}

// After (R2DBC)
public interface UserRepository extends R2dbcRepository<User, UUID> {
    Mono<User> findByPrimaryEmail(String email);  // Reactive 타입
}
```

**Service 변환**:
```java
// Before (JPA)
@Transactional
public User createUser(CreateUserRequest request) {
    User user = new User();
    user.setDisplayName(request.getDisplayName());
    return userRepository.save(user);  // 동기 호출
}

// After (R2DBC)
@Transactional
public Mono<User> createUser(CreateUserRequest request) {
    User user = new User();
    user.setDisplayName(request.getDisplayName());
    return userRepository.save(user);  // Reactive 반환
}
```

#### 트레이드오프 분석

**얻은 것**:
- Non-blocking I/O로 높은 동시성 처리
- 적은 스레드로 더 많은 요청 처리 (기존 200 threads → 10 threads)
- WebSocket 네이티브 지원
- Market Data 서비스와의 완벽한 통합

**잃은 것**:
- JPA의 편리한 관계 매핑 (`@OneToMany` 미지원)
- 지연 로딩 (Lazy Loading) 불가능
- 러닝 커브 증가 (Reactive Programming)
- 디버깅 어려움 (stacktrace 복잡)

**대응 방안**:
```java
// 관계 매핑 대안: Repository에서 수동 조인
@Repository
public interface PortfolioRepository extends R2dbcRepository<Portfolio, UUID> {

    // 사용자의 포트폴리오 + 포지션 조회 (수동 조인)
    @Query("""
        SELECT p.*, pos.*
        FROM portfolios p
        LEFT JOIN positions pos ON p.portfolio_id = pos.portfolio_id
        WHERE p.user_id = :userId AND p.deleted_at IS NULL
    """)
    Flux<Portfolio> findAllByUserIdWithPositions(@Param("userId") UUID userId);
}
```

### 8.2 Flyway V8 마이그레이션 (2026-01-03)

**배경**:
- PostgreSQL ENUM 타입 사용 시 R2DBC 호환성 문제
- Enum 값 변경 시 마이그레이션 복잡도 증가

**변경 내용**:
```sql
-- V8__convert_enums_to_varchar.sql

-- 1. ENUM 타입 제거
ALTER TABLE users
    ALTER COLUMN status TYPE VARCHAR(32) USING status::VARCHAR,
    ADD CONSTRAINT users_status_chk CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'DELETED'));

-- 2. 모든 ENUM 컬럼에 CHECK 제약조건 추가
ALTER TABLE social_accounts
    ALTER COLUMN provider TYPE VARCHAR(32) USING provider::VARCHAR,
    ADD CONSTRAINT social_accounts_provider_chk CHECK (provider IN ('GOOGLE', 'KAKAO', 'NAVER', 'APPLE'));

-- ... (모든 ENUM 타입 변환)
```

**효과**:
- R2DBC와 완벽한 호환성
- Enum 값 추가 시 마이그레이션 간소화
- Java Enum과 자동 변환

### 8.3 테스트 환경 미구성 (현재 상태)

**현재 상황**:
- 테스트 코드 없음
- `application-test.yml` 미작성
- Testcontainers 미설정

**계획 (P0)**:
1. Testcontainers로 PostgreSQL 테스트 환경 구성
2. `@DataR2dbcTest`로 Repository 테스트 작성
3. `@SpringBootTest`로 통합 테스트 작성
4. MockWebServer로 외부 API 모킹

---

## 부록 A. 관련 문서

- [DB Schema](./db_schema.md) - 데이터베이스 스키마
- [Market Data Pipeline](./marketdata_pipeline.md) - 시세 수집 아키텍처

---

## 부록 B. 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DB_HOST` | PostgreSQL 호스트 | `localhost` |
| `DB_PORT` | PostgreSQL 포트 | `5432` |
| `DB_USER` | PostgreSQL 사용자 | `postgres` |
| `DB_PASSWORD` | PostgreSQL 비밀번호 | `postgres` |
| `DB_NAME` | 데이터베이스 이름 | `port_rally` |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379/0` |

---

## 부록 C. e2e 테스트 가이드

### PostgreSQL 접속 및 테이블 확인

```bash
# PostgreSQL 컨테이너 접속
docker exec -it port-rally-postgres-1 psql -U postgres -d port_rally

# 테이블 목록 확인
\dt

# 특정 테이블 구조 확인
\d users

# 데이터 조회
SELECT * FROM users;

# 나가기
\q
```

### Redis 접속 및 확인

```bash
# Redis 컨테이너 접속
docker exec -it port-rally-redis-1 redis-cli

# 모든 키 확인
KEYS *

# 특정 키 조회
GET quote:005930

# 나가기
exit
```

### Swagger UI

```
http://localhost:8080/swagger-ui.html
```
