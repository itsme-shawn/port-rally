# PortRally Spring Boot + R2DBC 구현 현황

> **기술 스택**: Spring Boot 3.5.8 + WebFlux + R2DBC + Flyway
> **패키지 베이스**: `api`
> **참조 문서**: [db_schema.md](db_schema.md)

---

## 1. 구현 완료 현황

### 1.1 설정 파일

| 파일 | 상태 | 설명 |
|------|------|------|
| `build.gradle` | ✅ 완료 | Flyway, R2DBC, Redis, Security 의존성 |
| `application.yml` | ✅ 완료 | R2DBC, Flyway, Redis, SpringDoc 설정 |
| `application-local.yml` | ✅ 완료 | 로컬 개발 환경 설정 |

### 1.2 Config 클래스 (3개)

| 파일 | 상태 |
|------|------|
| `R2dbcConfig.java` | ✅ 완료 |
| `SecurityConfig.java` | ✅ 완료 |
| `GlobalExceptionHandler.java` | ✅ 완료 |

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

### 1.4 Enum 클래스 (13개)

```
src/main/java/api/enums/
├── user/
│   ├── UserStatus.java
│   ├── SocialProvider.java
│   └── RiskTolerance.java
├── portfolio/
│   ├── InsightStatus.java
│   └── SourceType.java
├── asset/
│   ├── AssetType.java
│   └── Recommendation.java
├── ocr/
│   ├── UploadStatus.java
│   └── OcrStatus.java
└── notification/
    ├── NotificationCategory.java
    ├── NotificationPriority.java
    ├── DeliveryChannel.java
    └── DeliveryStatus.java
```

### 1.5 Entity 클래스 (17개)

```
src/main/java/api/domain/
├── user/
│   ├── User.java
│   ├── SocialAccount.java
│   └── UserPreference.java
├── portfolio/
│   ├── Portfolio.java
│   ├── Position.java
│   ├── PortfolioMetric.java
│   └── PortfolioAiInsight.java
├── asset/
│   ├── Asset.java
│   ├── AssetMetric.java
│   └── AssetAiInsight.java
├── ocr/
│   ├── UploadedImage.java
│   ├── OcrResult.java
│   └── OcrDetectedPosition.java
├── news/
│   ├── NewsArticle.java
│   └── NewsAssetRelation.java
├── notification/
│   ├── NotificationType.java
│   ├── UserNotificationSetting.java
│   └── NotificationLog.java
└── audit/
    └── AuditLog.java
```

### 1.6 Repository 인터페이스 (16개)

```
src/main/java/api/repository/
├── user/
│   ├── UserRepository.java
│   ├── SocialAccountRepository.java
│   └── UserPreferenceRepository.java
├── portfolio/
│   ├── PortfolioRepository.java
│   ├── PositionRepository.java
│   ├── PortfolioMetricRepository.java
│   └── PortfolioAiInsightRepository.java
├── asset/
│   ├── AssetRepository.java
│   ├── AssetMetricRepository.java
│   └── AssetAiInsightRepository.java
├── ocr/
│   ├── UploadedImageRepository.java
│   ├── OcrResultRepository.java
│   └── OcrDetectedPositionRepository.java
├── news/
│   ├── NewsArticleRepository.java
│   └── NewsAssetRelationRepository.java
├── notification/
│   ├── NotificationTypeRepository.java
│   ├── UserNotificationSettingRepository.java
│   └── NotificationLogRepository.java
└── audit/
    └── AuditLogRepository.java
```

### 1.7 Service / Controller / DTO (User 도메인)

| 파일 | 상태 |
|------|------|
| `UserService.java` | ✅ 완료 |
| `UserController.java` | ✅ 완료 |
| `CreateUserRequest.java` | ✅ 완료 |
| `UserResponse.java` | ✅ 완료 |

---

## 2. 현재 파일 구조

```
apps/core-api/
├── build.gradle
└── src/main/
    ├── java/api/
    │   ├── CoreApiApplication.java
    │   ├── config/
    │   │   ├── R2dbcConfig.java
    │   │   ├── SecurityConfig.java
    │   │   └── GlobalExceptionHandler.java
    │   ├── controller/
    │   │   └── UserController.java
    │   ├── service/
    │   │   └── user/UserService.java
    │   ├── dto/
    │   │   └── user/
    │   │       ├── CreateUserRequest.java
    │   │       └── UserResponse.java
    │   ├── domain/         # 17개 Entity
    │   ├── enums/          # 13개 Enum
    │   └── repository/     # 16개 Repository
    └── resources/
        ├── application.yml
        ├── application-local.yml
        └── db/migration/   # 8개 SQL
```

---

## 3. TODO

### P0 - 필수

- [ ] 테스트 환경 설정 (`application-test.yml`, Testcontainers)

### P1 - 핵심 기능

- [ ] Service 계층 확장 (Portfolio, Asset, Notification)
- [ ] Controller 계층 확장
- [ ] DTO 클래스 확장

### P2 - 통합 기능

- [ ] OAuth2 인증 (Google, Kakao, Naver, Apple)
- [ ] JWT 토큰 발급/검증
- [ ] Redis 연동 (현재가 캐시, Pub/Sub)
- [ ] WebSocket 실시간 시세

### P3 - 부가 기능

- [ ] 모니터링 (Actuator, Micrometer)
- [ ] Kafka 연동 (AI Agent 작업)

---

## 4. R2DBC 참고사항

### JPA와의 차이점

| 항목 | JPA | R2DBC |
|------|-----|-------|
| 관계 매핑 | `@OneToMany` | 지원 안함 (수동 조인) |
| 지연 로딩 | `FetchType.LAZY` | 없음 |
| ID 생성 | `@GeneratedValue` | DB 기본값 |

### ENUM 처리

V8 마이그레이션에서 PostgreSQL ENUM → VARCHAR로 변환 완료.
Java Enum은 String으로 자동 변환됨.

---

## 5. 참고 문서

- [db_schema.md](db_schema.md) - DB 스키마 설계
- [springboot_work_log.md](springboot_work_log.md) - 작업 내역
