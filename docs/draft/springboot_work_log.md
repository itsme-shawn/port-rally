# Spring Boot Core API 작업 내역

> **프로젝트**: `apps/core-api`
> **기술 스택**: Spring Boot 3.5.8 + WebFlux + R2DBC + Flyway
> **최종 수정**: 2026-01-03

---

## 1. 구현 완료

### 1.1 프로젝트 설정

| 파일 | 내용 |
|------|------|
| `build.gradle` | Spring Boot 3.5.8, WebFlux, R2DBC, Flyway, Redis, Security, SpringDoc |
| `application.yml` | R2DBC, Flyway, Redis, Actuator, SpringDoc 설정 |
| `application-local.yml` | 로컬 개발 환경 (localhost 연결) |

### 1.2 Config 클래스

| 파일 | 설명 |
|------|------|
| `R2dbcConfig.java` | R2DBC Auditing, Repository 스캔 |
| `SecurityConfig.java` | Spring Security WebFlux 설정 |
| `GlobalExceptionHandler.java` | 전역 예외 처리 |

### 1.3 Flyway 마이그레이션 (8개)

| 파일 | 테이블 |
|------|--------|
| `V1__create_user_tables.sql` | users, social_accounts, user_preferences |
| `V2__create_asset_tables.sql` | assets_master, assets_metrics, asset_ai_insights |
| `V3__create_portfolio_tables.sql` | portfolios, positions, portfolio_metrics, portfolio_ai_insights |
| `V4__create_ocr_tables.sql` | uploaded_images, ocr_results, ocr_detected_positions |
| `V5__create_news_tables.sql` | news_articles, news_asset_relations |
| `V6__create_notification_tables.sql` | notification_types, user_notification_settings, notifications_logs |
| `V7__create_audit_tables.sql` | audit_logs |
| `V8__convert_enums_to_varchar.sql` | PostgreSQL ENUM → VARCHAR 변환 |

**총 19개 테이블**

### 1.4 도메인 계층

| 구분 | 개수 | 패키지 |
|------|------|--------|
| Enum | 13개 | `api.enums.*` |
| Entity | 17개 | `api.domain.*` |
| Repository | 16개 | `api.repository.*` |

### 1.5 User API (MVP)

| 파일 | 설명 |
|------|------|
| `UserController.java` | REST API 엔드포인트 |
| `UserService.java` | 비즈니스 로직 |
| `CreateUserRequest.java` | 요청 DTO |
| `UserResponse.java` | 응답 DTO |

---

## 2. 파일 구조

```
apps/core-api/src/main/
├── java/api/
│   ├── CoreApiApplication.java
│   ├── config/
│   │   ├── R2dbcConfig.java
│   │   ├── SecurityConfig.java
│   │   └── GlobalExceptionHandler.java
│   ├── controller/
│   │   └── UserController.java
│   ├── service/user/
│   │   └── UserService.java
│   ├── dto/user/
│   │   ├── CreateUserRequest.java
│   │   └── UserResponse.java
│   ├── domain/          # 17개 Entity
│   ├── enums/           # 13개 Enum
│   └── repository/      # 16개 Repository
└── resources/
    ├── application.yml
    ├── application-local.yml
    └── db/migration/    # 8개 SQL
```

---

## 3. 실행 방법

### 로컬 개발

```bash
# 1. Docker 인프라 실행
docker-compose up -d postgres redis

# 2. 애플리케이션 실행
cd apps/core-api
./run-local.sh
# 또는
DB_HOST=localhost ./gradlew bootRun --args='--spring.profiles.active=local'
```

### API 테스트

```bash
# Health Check
curl http://localhost:8080/actuator/health

# Swagger UI
open http://localhost:8080/swagger-ui.html
```

---

## 4. TODO

### P0 - 필수
- [ ] 테스트 환경 설정 (Testcontainers)

### P1 - 핵심 기능
- [ ] Service/Controller 확장 (Portfolio, Asset, Notification)
- [ ] DTO 클래스 확장

### P2 - 통합 기능
- [ ] OAuth2 인증
- [ ] JWT 토큰
- [ ] Redis 연동
- [ ] WebSocket

### P3 - 부가 기능
- [ ] 모니터링
- [ ] Kafka 연동

---

## 5. 참고

- [springboot_r2dbc_plan.md](springboot_r2dbc_plan.md) - 구현 현황
- [db_schema.md](db_schema.md) - DB 스키마
