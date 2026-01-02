# PortRally Database Schema Design (JPA version)

> **투자보조 AI 서비스** - Spring Data JPA Entity 설계를 위한 상세 스키마 문서

현재는 JPA 대신 R2DBC 를 채택해서 Deprecated 됨

---

## 📋 목차

1. [사용자 관리 (User Management)](#1-사용자-관리)
2. [포트폴리오 (Portfolio)](#2-포트폴리오)
3. [종목/자산 (Assets)](#3-종목자산)
4. [보유 종목 (Positions)](#4-보유-종목)
5. [이미지 업로드 및 OCR](#5-이미지-업로드-및-ocr)
6. [뉴스 및 공시](#6-뉴스-및-공시)
7. [알림 시스템](#7-알림-시스템)

---

## 1. 사용자 관리

### 1.1 users

**목적**: 사용자 계정 정보 저장

**Entity 정보**:
- Package: `com.portrally.domain.user`
- Class: `User`
- Table: `users`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| userId | UUID | UUID | `@Id @GeneratedValue` | PK |
| status | UserStatus (enum) | VARCHAR/ENUM | `@Enumerated(EnumType.STRING)` | PENDING, ACTIVE, SUSPENDED, DELETED |
| displayName | String | VARCHAR(100) | `@Column(length=100)` | 닉네임 |
| primaryEmail | String | VARCHAR(255) | `@Column(unique=true)` | 주 이메일 |
| primaryEmailVerified | Boolean | BOOLEAN | `@Column(nullable=false)` | 이메일 인증 여부 |
| profileImageUrl | String | TEXT | `@Column(columnDefinition="TEXT")` | 프로필 이미지 URL |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |
| lastLoginAt | Instant | TIMESTAMPTZ | - | 마지막 로그인 |
| signupCompletedAt | Instant | TIMESTAMPTZ | - | 가입 완료 시각 |
| termsAcceptedAt | Instant | TIMESTAMPTZ | - | 약관 동의 시각 |
| deletedAt | Instant | TIMESTAMPTZ | - | 소프트 삭제 시각 |

**관계 (Relationships)**:
```java
@OneToMany(mappedBy = "user")
private List<SocialAccount> socialAccounts;

@OneToOne(mappedBy = "user")
private UserPreference userPreference;

@OneToMany(mappedBy = "user")
private List<Portfolio> portfolios;

@OneToMany(mappedBy = "user")
private List<UploadedImage> uploadedImages;

@OneToMany(mappedBy = "user")
private List<UserNotificationSetting> notificationSettings;

@OneToMany(mappedBy = "user")
private List<NotificationLog> notificationLogs;
```

**인덱스**:
- `UNIQUE(primary_email) WHERE primary_email IS NOT NULL`
- `INDEX(status)`
- `INDEX(created_at)`

**UserStatus Enum**:
```java
public enum UserStatus {
    PENDING,    // 가입 진행중
    ACTIVE,     // 활성
    SUSPENDED,  // 정지
    DELETED     // 삭제
}
```

---

### 1.2 social_accounts

**목적**: 소셜 로그인 연동 정보

**Entity 정보**:
- Package: `com.portrally.domain.user`
- Class: `SocialAccount`
- Table: `social_accounts`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| socialAccountId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK to users |
| provider | SocialProvider (enum) | VARCHAR/ENUM | `@Enumerated(EnumType.STRING)` | google, kakao, naver, apple |
| providerUserId | String | VARCHAR(255) | `@Column(nullable=false)` | 제공자의 사용자 ID |
| providerEmail | String | VARCHAR(255) | - | 제공자 이메일 |
| providerEmailVerified | Boolean | BOOLEAN | - | 제공자 측 인증 여부 |
| scopes | String | TEXT | `@Column(columnDefinition="TEXT")` | OAuth 스코프 (JSON or comma-separated) |
| linkedAt | Instant | TIMESTAMPTZ | - | 연결 시각 |
| lastLoginAt | Instant | TIMESTAMPTZ | - | 마지막 로그인 |
| isActive | Boolean | BOOLEAN | `@Column(nullable=false)` | 연결 활성 여부 |
| revokedAt | Instant | TIMESTAMPTZ | - | 연결 해제 시각 |

**제약조건**:
```java
@Table(
    uniqueConstraints = {
        @UniqueConstraint(columnNames = {"provider", "provider_user_id"}),
        @UniqueConstraint(columnNames = {"user_id", "provider"})
    }
)
```

**인덱스**:
- `INDEX(user_id)`

**SocialProvider Enum**:
```java
public enum SocialProvider {
    GOOGLE,
    KAKAO,
    NAVER,
    APPLE
}
```

---

### 1.3 user_preferences

**목적**: 사용자 개인 설정 (1:1 관계)

**Entity 정보**:
- Package: `com.portrally.domain.user`
- Class: `UserPreference`
- Table: `user_preferences`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| user | User | UUID | `@Id @OneToOne @JoinColumn(name="user_id")` | PK & FK |
| notificationEnabled | Boolean | BOOLEAN | `@Column(nullable=false)` | 알림 활성화 |
| darkMode | Boolean | BOOLEAN | `@Column(nullable=false)` | 다크모드 |
| riskTolerance | RiskTolerance (enum) | VARCHAR/ENUM | `@Enumerated(EnumType.STRING)` | 투자 성향 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |

**RiskTolerance Enum**:
```java
public enum RiskTolerance {
    CONSERVATIVE,  // 보수적
    MODERATE,      // 중립적
    AGGRESSIVE     // 공격적
}
```

---

### 1.4 audit_logs

**목적**: 사용자 활동 감사 로그

**Entity 정보**:
- Package: `com.portrally.domain.audit`
- Class: `AuditLog`
- Table: `audit_logs`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| auditLogId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK (nullable) |
| eventType | String | VARCHAR(100) | `@Column(nullable=false)` | 이벤트 타입 |
| metadata | String | JSONB | `@Column(columnDefinition="jsonb")` | 메타데이터 (JSON) |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 발생 시각 |

**이벤트 타입 예시**:
- `LOGIN`
- `LINK_SOCIAL`
- `PORTFOLIO_CREATE`
- `IMAGE_UPLOAD`
- `POSITION_ADD`
- etc.

---

## 2. 포트폴리오

### 2.1 portfolios

**목적**: 사용자의 포트폴리오 (1명의 사용자가 여러 포트폴리오 소유 가능)

**Entity 정보**:
- Package: `com.portrally.domain.portfolio`
- Class: `Portfolio`
- Table: `portfolios`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| portfolioId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK to users |
| portfolioName | String | VARCHAR(100) | `@Column(nullable=false)` | 포트폴리오 이름 |
| isPrimary | Boolean | BOOLEAN | `@Column(nullable=false)` | 대표 포트폴리오 여부 |
| baseCurrency | String | VARCHAR(10) | `@Column(nullable=false)` | 기준 통화 (KRW, USD) |
| investmentType | String | VARCHAR(50) | - | 투자 유형 (선택) |
| goal | String | VARCHAR(50) | - | 투자 목표 (선택) |
| sectorFocus | String | VARCHAR(100) | - | 집중 섹터 (선택) |
| tags | String | JSONB | `@Column(columnDefinition="jsonb")` | 태그 (선택) |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |
| deletedAt | Instant | TIMESTAMPTZ | - | 삭제일시 (soft delete) |

**관계**:
```java
@OneToMany(mappedBy = "portfolio")
private List<Position> positions;

@OneToMany(mappedBy = "portfolio")
private List<PortfolioMetric> metrics;

@OneToMany(mappedBy = "portfolio")
private List<PortfolioAiInsight> aiInsights;
```

---

### 2.2 portfolio_metrics

**목적**: 포트폴리오의 일별 성과 추적 및 지표

**Entity 정보**:
- Package: `com.portrally.domain.portfolio`
- Class: `PortfolioMetric`
- Table: `portfolio_metrics`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| portfolioMetricsId | UUID | UUID | `@Id @GeneratedValue` | PK |
| portfolio | Portfolio | UUID | `@ManyToOne @JoinColumn(name="portfolio_id")` | FK to portfolios |
| snapshotDate | LocalDate | DATE | `@Column(nullable=false)` | 스냅샷 날짜 |
| totalValue | BigDecimal | NUMERIC(28,8) | - | 총 평가액 |
| totalCost | BigDecimal | NUMERIC(28,8) | - | 총 투자금액 |
| totalPnl | BigDecimal | NUMERIC(28,8) | - | 총 손익 |
| totalPnlPercent | BigDecimal | NUMERIC(10,4) | - | 총 수익률 (%) |
| dailyPnlPercent | BigDecimal | NUMERIC(10,4) | - | 일일 수익률 |
| weeklyPnlPercent | BigDecimal | NUMERIC(10,4) | - | 주간 수익률 |
| monthlyPnlPercent | BigDecimal | NUMERIC(10,4) | - | 월간 수익률 |
| ytdPnlPercent | BigDecimal | NUMERIC(10,4) | - | 연초 대비 수익률 |
| volatility | BigDecimal | NUMERIC(10,6) | - | 변동성 (표준편차) |
| sharpeRatio | BigDecimal | NUMERIC(10,6) | - | 샤프 지수 |
| maxDrawdown | BigDecimal | NUMERIC(10,6) | - | 최대 낙폭 (%) |
| var95 | BigDecimal | NUMERIC(28,8) | - | VaR (95%) |
| beta | BigDecimal | NUMERIC(10,6) | - | 베타 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |

**제약조건**:
```java
@Table(
    uniqueConstraints = @UniqueConstraint(columnNames = {"portfolio_id", "snapshot_date"})
)
```

---

### 2.3 portfolio_ai_insights

**목적**: 포트폴리오 종합 AI 분석 (개인별)

**Entity 정보**:
- Package: `com.portrally.domain.portfolio`
- Class: `PortfolioAiInsight`
- Table: `portfolio_ai_insights`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| portfolioInsightId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK to users |
| portfolio | Portfolio | UUID | `@ManyToOne @JoinColumn(name="portfolio_id")` | FK to portfolios |
| insightType | String | VARCHAR(50) | `@Column(nullable=false)` | daily_report, weekly_review, etc. |
| analysisDate | LocalDate | DATE | `@Column(nullable=false)` | 분석 기준일 |
| title | String | VARCHAR(200) | `@Column(nullable=false)` | 제목 |
| executiveSummary | String | TEXT | `@Column(columnDefinition="TEXT")` | 핵심 요약 (3-5줄) |
| fullReport | String | TEXT | `@Column(nullable=false, columnDefinition="TEXT")` | 전체 리포트 (LLM 생성) |
| healthScore | BigDecimal | NUMERIC(5,4) | - | 포트폴리오 건강도 (0~1) |
| riskScore | BigDecimal | NUMERIC(5,4) | - | 리스크 점수 (0~1) |
| diversificationScore | BigDecimal | NUMERIC(5,4) | - | 분산도 점수 (0~1) |
| performanceScore | BigDecimal | NUMERIC(5,4) | - | 성과 점수 (0~1) |
| generatedBy | String | VARCHAR(50) | - | AI 모델명 |
| version | Integer | INTEGER | `@Column(nullable=false)` | 리포트 버전 |
| status | InsightStatus (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | active, superseded, archived |
| isRead | Boolean | BOOLEAN | `@Column(nullable=false)` | 읽음 여부 |
| readAt | Instant | TIMESTAMPTZ | - | 읽은 시각 |
| generatedAt | Instant | TIMESTAMPTZ | `@Column(nullable=false)` | AI 생성 시각 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 레코드 생성 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 레코드 수정 |

**제약조건**:
```java
@Table(
    uniqueConstraints = @UniqueConstraint(
        columnNames = {"portfolio_id", "insight_type", "analysis_date"}
    )
)
```

**인덱스**:
- `INDEX(user_id, analysis_date DESC)`
- `INDEX(portfolio_id, insight_type, analysis_date DESC)`
- `INDEX(user_id, is_read, created_at DESC)`
- `INDEX(status, generated_at DESC)`

**InsightStatus Enum**:
```java
public enum InsightStatus {
    ACTIVE,      // 활성 (최신)
    SUPERSEDED,  // 대체됨 (새 버전 생성됨)
    ARCHIVED     // 보관됨
}
```

---

## 3. 종목/자산

### 3.1 assets_master

**목적**: 투자 가능한 모든 자산의 마스터 정보

**Entity 정보**:
- Package: `com.portrally.domain.asset`
- Class: `Asset`
- Table: `assets_master`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| assetId | UUID | UUID | `@Id @GeneratedValue` | PK |
| symbol | String | VARCHAR(50) | `@Column(nullable=false)` | 티커/심볼 |
| market | String | VARCHAR(50) | `@Column(nullable=false)` | KRX, NASDAQ, NYSE, etc. |
| assetType | AssetType (enum) | VARCHAR(50) | `@Enumerated(EnumType.STRING)` | stock, etf, crypto |
| name | String | VARCHAR(255) | - | 종목명 |
| sector | String | VARCHAR(100) | - | 섹터 |
| industry | String | VARCHAR(100) | - | 산업 |
| country | String | VARCHAR(10) | - | 국가 코드 |
| currency | String | VARCHAR(10) | - | 거래 통화 |
| isActive | Boolean | BOOLEAN | `@Column(nullable=false)` | 상장 여부 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |

**제약조건**:
```java
@Table(
    uniqueConstraints = @UniqueConstraint(columnNames = {"market", "symbol", "asset_type"})
)
```

**관계**:
```java
@OneToMany(mappedBy = "asset")
private List<AssetAiInsight> aiInsights;

@OneToMany(mappedBy = "asset")
private List<NewsAssetRelation> newsRelations;

@OneToOne(mappedBy = "asset")
private AssetMetric metrics;

@OneToMany(mappedBy = "asset")
private List<Position> positions;
```

**AssetType Enum**:
```java
public enum AssetType {
    STOCK,   // 주식
    ETF,     // 상장지수펀드
    CRYPTO,  // 암호화폐
    BOND,    // 채권
    CASH     // 현금성 자산
}
```

---

### 3.2 assets_metrics

**목적**: 종목별 기술적 지표

**Entity 정보**:
- Package: `com.portrally.domain.asset`
- Class: `AssetMetric`
- Table: `assets_metrics`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| indicatorId | UUID | UUID | `@Id @GeneratedValue` | PK |
| assetInsight | AssetAiInsight | UUID | `@ManyToOne @JoinColumn(name="asset_insight_id")` | FK |
| rsi14 | BigDecimal | NUMERIC(10,4) | - | RSI (14일) |
| macdValue | BigDecimal | NUMERIC(28,8) | - | MACD 값 |
| macdSignal | BigDecimal | NUMERIC(28,8) | - | MACD 시그널 |
| ma20 | BigDecimal | NUMERIC(28,8) | - | 20일 이동평균 |
| ma50 | BigDecimal | NUMERIC(28,8) | - | 50일 이동평균 |
| ma200 | BigDecimal | NUMERIC(28,8) | - | 200일 이동평균 |
| bollingerUpper | BigDecimal | NUMERIC(28,8) | - | 볼린저 밴드 상단 |
| bollingerMiddle | BigDecimal | NUMERIC(28,8) | - | 볼린저 밴드 중간 |
| bollingerLower | BigDecimal | NUMERIC(28,8) | - | 볼린저 밴드 하단 |
| volumeAvg20 | Long | BIGINT | - | 20일 평균 거래량 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |

---

### 3.3 asset_ai_insights

**목적**: 종목별 AI 분석 (전체 사용자 공용)

**Entity 정보**:
- Package: `com.portrally.domain.asset`
- Class: `AssetAiInsight`
- Table: `asset_ai_insights`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| assetInsightId | UUID | UUID | `@Id @GeneratedValue` | PK |
| asset | Asset | UUID | `@ManyToOne @JoinColumn(name="asset_id")` | FK to assets |
| insightType | String | VARCHAR(50) | `@Column(nullable=false)` | daily_summary, technical_analysis, etc. |
| analysisDate | LocalDate | DATE | `@Column(nullable=false)` | 분석 기준일 |
| title | String | VARCHAR(200) | `@Column(nullable=false)` | 제목 |
| summary | String | TEXT | `@Column(columnDefinition="TEXT")` | 핵심 요약 |
| content | String | TEXT | `@Column(nullable=false, columnDefinition="TEXT")` | 상세 분석 (LLM 생성) |
| sentimentScore | BigDecimal | NUMERIC(5,4) | - | 감성 점수 (-1~1) |
| technicalScore | BigDecimal | NUMERIC(5,4) | - | 기술적 점수 (0~1) |
| fundamentalScore | BigDecimal | NUMERIC(5,4) | - | 펀더멘털 점수 (0~1) |
| overallScore | BigDecimal | NUMERIC(5,4) | - | 종합 점수 (0~1) |
| recommendation | Recommendation (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | 매매 추천 |
| confidenceLevel | BigDecimal | NUMERIC(5,4) | - | AI 신뢰도 (0~1) |
| priceAtAnalysis | BigDecimal | NUMERIC(28,8) | - | 분석 시점 가격 |
| targetPrice | BigDecimal | NUMERIC(28,8) | - | 목표가 |
| supportPrice | BigDecimal | NUMERIC(28,8) | - | 지지선 |
| resistancePrice | BigDecimal | NUMERIC(28,8) | - | 저항선 |
| keyFactors | String | TEXT | `@Column(columnDefinition="TEXT")` | 주요 판단 근거 |
| riskFactors | String | TEXT | `@Column(columnDefinition="TEXT")` | 리스크 요인 |
| generatedBy | String | VARCHAR(50) | - | AI 모델명 |
| version | Integer | INTEGER | `@Column(nullable=false)` | 분석 버전 |
| status | InsightStatus (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | active, superseded, archived |
| viewCount | Integer | INTEGER | `@Column(nullable=false)` | 조회수 |
| generatedAt | Instant | TIMESTAMPTZ | `@Column(nullable=false)` | AI 생성 시각 |
| expiresAt | Instant | TIMESTAMPTZ | - | 유효기간 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 레코드 생성 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 레코드 수정 |

**제약조건**:
```java
@Table(
    uniqueConstraints = @UniqueConstraint(
        columnNames = {"asset_id", "insight_type", "analysis_date"}
    )
)
```

**인덱스**:
- `INDEX(asset_id, analysis_date DESC)`
- `INDEX(insight_type, analysis_date DESC)`
- `INDEX(recommendation, analysis_date DESC)`
- `INDEX(status, generated_at DESC)`

**Recommendation Enum**:
```java
public enum Recommendation {
    STRONG_BUY,   // 적극 매수
    BUY,          // 매수
    HOLD,         // 보유
    SELL,         // 매도
    STRONG_SELL   // 적극 매도
}
```

---

## 4. 보유 종목

### 4.1 positions

**목적**: 포트폴리오별 종목 보유 현황 (Portfolio ↔ Asset 연결 테이블)

**Entity 정보**:
- Package: `com.portrally.domain.portfolio`
- Class: `Position`
- Table: `positions`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| positionId | UUID | UUID | `@Id @GeneratedValue` | PK |
| portfolio | Portfolio | UUID | `@ManyToOne @JoinColumn(name="portfolio_id")` | FK to portfolios |
| asset | Asset | UUID | `@ManyToOne @JoinColumn(name="asset_id")` | FK to assets |
| quantity | BigDecimal | NUMERIC(28,8) | `@Column(nullable=false)` | 보유 수량 |
| averageCost | BigDecimal | NUMERIC(28,8) | - | 평균 단가 |
| costBasis | BigDecimal | NUMERIC(28,8) | - | 총 매입원가 |
| sourceType | SourceType (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | manual, ocr |
| value | BigDecimal | NUMERIC(28,8) | `@Column(nullable=false)` | 평가금액 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |
| deletedAt | Instant | TIMESTAMPTZ | - | 삭제일시 (soft delete) ⚠️ 추가 필요 |

**SourceType Enum**:
```java
public enum SourceType {
    MANUAL,  // 수기 입력
    OCR      // 이미지 인식
}
```

**인덱스**:
- `INDEX(portfolio_id, asset_id)`
- `INDEX(portfolio_id, deleted_at)` (soft delete 고려)

---

## 5. 이미지 업로드 및 OCR

### 5.1 uploaded_images

**목적**: 사용자가 업로드한 계좌 이미지

**Entity 정보**:
- Package: `com.portrally.domain.ocr`
- Class: `UploadedImage`
- Table: `uploaded_images`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| imageId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK to users |
| portfolio | Portfolio | UUID | `@ManyToOne @JoinColumn(name="portfolio_id")` | FK (선택) |
| storageUrl | String | TEXT | `@Column(nullable=false, columnDefinition="TEXT")` | S3 URL |
| uploadStatus | UploadStatus (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | pending, processing, completed, failed |
| contentType | String | VARCHAR(100) | - | MIME 타입 |
| fileSize | Long | BIGINT | - | 파일 크기 (bytes) |
| hashSha256 | String | CHAR(64) | - | 파일 해시 (중복 방지) |
| retentionPolicy | String | VARCHAR(50) | `@Column(nullable=false)` | 보관 정책 |
| retainUntil | Instant | TIMESTAMPTZ | - | 보관 만료일 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 업로드 시각 |

**관계**:
```java
@OneToOne(mappedBy = "image")
private OcrResult ocrResult;
```

**UploadStatus Enum**:
```java
public enum UploadStatus {
    PENDING,     // 대기중
    PROCESSING,  // 처리중
    COMPLETED,   // 완료
    FAILED       // 실패
}
```

---

### 5.2 ocr_results

**목적**: AI가 이미지에서 추출한 OCR 결과

**Entity 정보**:
- Package: `com.portrally.domain.ocr`
- Class: `OcrResult`
- Table: `ocr_results`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| ocrResultId | UUID | UUID | `@Id @GeneratedValue` | PK |
| image | UploadedImage | UUID | `@OneToOne @JoinColumn(name="image_id")` | FK (1:1) |
| status | OcrStatus (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | pending, verified, rejected, failed |
| rawText | String | TEXT | `@Column(columnDefinition="TEXT")` | OCR 원문 |
| parsedData | String | JSONB | `@Column(columnDefinition="jsonb")` | 구조화된 데이터 (JSON) |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |

**관계**:
```java
@OneToMany(mappedBy = "ocrResult")
private List<OcrDetectedPosition> detectedPositions;
```

**OcrStatus Enum**:
```java
public enum OcrStatus {
    PENDING,   // 인식 대기
    VERIFIED,  // 사용자 확인 완료
    REJECTED,  // 사용자 거부
    FAILED     // 인식 실패
}
```

---

### 5.3 ocr_detected_positions

**목적**: OCR로 감지된 종목 정보 (사용자 확인 전)

**Entity 정보**:
- Package: `com.portrally.domain.ocr`
- Class: `OcrDetectedPosition`
- Table: `ocr_detected_positions`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| ocrDetectedPositionId | UUID | UUID | `@Id @GeneratedValue` | PK |
| ocrResult | OcrResult | UUID | `@ManyToOne @JoinColumn(name="ocr_result_id")` | FK to ocr_results |
| detectedSymbol | String | VARCHAR(50) | - | OCR 인식 심볼 |
| detectedName | String | VARCHAR(255) | - | OCR 인식 종목명 |
| detectedMarket | String | VARCHAR(50) | - | OCR 인식 시장 |
| quantity | BigDecimal | NUMERIC(28,8) | - | 인식된 수량 |
| averageCost | BigDecimal | NUMERIC(28,8) | - | 인식된 평단가 |
| matchAsset | Asset | UUID | `@ManyToOne @JoinColumn(name="match_asset_id")` | 매칭된 자산 (FK) |
| matchConfidence | BigDecimal | NUMERIC(5,4) | - | 매칭 신뢰도 (0~1) |
| isConfirmed | Boolean | BOOLEAN | `@Column(nullable=false)` | 사용자 확인 여부 |
| confirmedAt | Instant | TIMESTAMPTZ | - | 확정 시각 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |

**워크플로우**:
1. OCR 인식 → `ocr_detected_positions` 생성
2. 사용자 확인 → `isConfirmed = true`
3. `positions` 테이블에 upsert (portfolio_id + asset_id 기준)
4. `sourceType = OCR` 설정

---

## 6. 뉴스 및 공시

### 6.1 news_articles

**목적**: 뉴스 기사 저장

**Entity 정보**:
- Package: `com.portrally.domain.news`
- Class: `NewsArticle`
- Table: `news_articles`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| newsId | UUID | UUID | `@Id @GeneratedValue` | PK |
| source | String | VARCHAR(100) | `@Column(nullable=false)` | 출처 |
| sourceUrl | String | TEXT | `@Column(unique=true, columnDefinition="TEXT")` | 원문 URL (중복 방지) |
| title | String | TEXT | `@Column(nullable=false, columnDefinition="TEXT")` | 제목 |
| content | String | TEXT | `@Column(columnDefinition="TEXT")` | 본문 |
| summary | String | TEXT | `@Column(columnDefinition="TEXT")` | 요약 |
| publishedAt | Instant | TIMESTAMPTZ | `@Column(nullable=false)` | 발행일시 |
| sentimentScore | BigDecimal | NUMERIC(5,4) | - | 감성 점수 (-1~1) |
| impactScore | BigDecimal | NUMERIC(5,4) | - | 영향력 점수 (0~1) |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 수집일시 |

**관계**:
```java
@OneToMany(mappedBy = "newsArticle")
private List<NewsAssetRelation> assetRelations;
```

---

### 6.2 news_asset_relations

**목적**: 뉴스와 종목의 연결 테이블 (N:N)

**Entity 정보**:
- Package: `com.portrally.domain.news`
- Class: `NewsAssetRelation`
- Table: `news_asset_relations`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| newsAssetRelationId | UUID | UUID | `@Id @GeneratedValue` | PK |
| newsArticle | NewsArticle | UUID | `@ManyToOne @JoinColumn(name="news_id")` | FK to news_articles |
| asset | Asset | UUID | `@ManyToOne @JoinColumn(name="asset_id")` | FK to assets |
| relevanceScore | BigDecimal | NUMERIC(5,4) | - | 연관도 점수 (0~1) |

**제약조건**:
```java
@Table(
    uniqueConstraints = @UniqueConstraint(columnNames = {"news_id", "asset_id"})
)
```

---

## 7. 알림 시스템

### 7.1 notification_types

**목적**: 시스템에서 제공하는 알림 종류 정의 (마스터 데이터)

**Entity 정보**:
- Package: `com.portrally.domain.notification`
- Class: `NotificationType`
- Table: `notification_types`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| notificationTypeId | UUID | UUID | `@Id @GeneratedValue` | PK |
| typeName | String | VARCHAR(100) | `@Column(unique=true, nullable=false)` | 알림 타입명 |
| category | NotificationCategory (enum) | VARCHAR(50) | `@Enumerated(EnumType.STRING)` | ai, market, system |
| description | String | TEXT | `@Column(columnDefinition="TEXT")` | 설명 |
| defaultEnabled | Boolean | BOOLEAN | `@Column(nullable=false)` | 신규 가입자 기본 설정 |
| defaultChannels | String | VARCHAR(200) | `@Column(nullable=false)` | 기본 채널 (push,email) |
| isUserConfigurable | Boolean | BOOLEAN | `@Column(nullable=false)` | 사용자 설정 가능 여부 |
| priority | NotificationPriority (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | low, normal, high, urgent |
| icon | String | VARCHAR(50) | - | UI 아이콘 |
| isActive | Boolean | BOOLEAN | `@Column(nullable=false)` | 현재 제공 여부 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |

**인덱스**:
- `INDEX(category, is_active)`

**NotificationCategory Enum**:
```java
public enum NotificationCategory {
    AI,      // AI 분석 관련
    MARKET,  // 시장 변동 관련
    SYSTEM   // 시스템 알림
}
```

**NotificationPriority Enum**:
```java
public enum NotificationPriority {
    LOW,
    NORMAL,
    HIGH,
    URGENT
}
```

---

### 7.2 user_notification_settings

**목적**: 사용자별 알림 수신 설정 (User ↔ NotificationType 연결 테이블)

**Entity 정보**:
- Package: `com.portrally.domain.notification`
- Class: `UserNotificationSetting`
- Table: `user_notification_settings`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| settingsId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK to users |
| notificationType | NotificationType | UUID | `@ManyToOne @JoinColumn(name="notification_type_id")` | FK |
| isEnabled | Boolean | BOOLEAN | `@Column(nullable=false)` | 수신 여부 |
| deliveryChannels | String | VARCHAR(200) | `@Column(nullable=false)` | 수신 채널 (push,email,sms) |
| quietHoursStart | LocalTime | TIME | - | 방해금지 시작 |
| quietHoursEnd | LocalTime | TIME | - | 방해금지 종료 |
| preferredTime | LocalTime | TIME | - | 선호 수신 시간 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |
| updatedAt | Instant | TIMESTAMPTZ | `@LastModifiedDate` | 수정일시 |

**제약조건**:
```java
@Table(
    uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "notification_type_id"})
)
```

**인덱스**:
- `INDEX(user_id, is_enabled)`

---

### 7.3 notifications_logs

**목적**: 실제 발송된 알림의 기록 및 상태 관리

**Entity 정보**:
- Package: `com.portrally.domain.notification`
- Class: `NotificationLog`
- Table: `notifications_logs`

**필드 정의**:

| 필드명 | Java 타입 | DB 타입 | JPA 애노테이션 | 설명 |
|--------|----------|---------|---------------|------|
| notificationLogId | UUID | UUID | `@Id @GeneratedValue` | PK |
| user | User | UUID | `@ManyToOne @JoinColumn(name="user_id")` | FK to users |
| notificationType | NotificationType | UUID | `@ManyToOne @JoinColumn(name="notification_type_id")` | FK |
| title | String | VARCHAR(200) | `@Column(nullable=false)` | 알림 제목 |
| message | String | TEXT | `@Column(nullable=false, columnDefinition="TEXT")` | 알림 본문 |
| deliveryChannel | DeliveryChannel (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | 발송 채널 |
| deliveryStatus | DeliveryStatus (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | pending, sent, failed, read |
| priority | NotificationPriority (enum) | VARCHAR(20) | `@Enumerated(EnumType.STRING)` | 우선순위 |
| sourceType | String | VARCHAR(50) | - | 출처 타입 |
| sourceId | UUID | UUID | - | 출처 레코드 ID (다형성) |
| relatedPortfolio | Portfolio | UUID | `@ManyToOne @JoinColumn(name="related_portfolio_id")` | 관련 포트폴리오 |
| relatedAsset | Asset | UUID | `@ManyToOne @JoinColumn(name="related_asset_id")` | 관련 종목 |
| actionUrl | String | TEXT | `@Column(columnDefinition="TEXT")` | 클릭 URL/딥링크 |
| isRead | Boolean | BOOLEAN | `@Column(nullable=false)` | 읽음 여부 |
| readAt | Instant | TIMESTAMPTZ | - | 읽은 시각 |
| sentAt | Instant | TIMESTAMPTZ | - | 발송 성공 시각 |
| failedReason | String | TEXT | `@Column(columnDefinition="TEXT")` | 발송 실패 사유 |
| retryCount | Integer | INTEGER | `@Column(nullable=false)` | 재시도 횟수 |
| createdAt | Instant | TIMESTAMPTZ | `@CreatedDate` | 생성일시 |

**인덱스**:
- `INDEX(user_id, is_read, created_at DESC)` - 읽지 않은 알림 조회
- `INDEX(user_id, notification_type_id, created_at DESC)`
- `INDEX(notification_type_id, created_at DESC)`
- `INDEX(delivery_status, created_at)` - 재처리용
- `INDEX(source_type, source_id)`

**DeliveryChannel Enum**:
```java
public enum DeliveryChannel {
    PUSH,   // 푸시 알림
    EMAIL,  // 이메일
    SMS,    // 문자메시지
    IN_APP  // 인앱 알림
}
```

**DeliveryStatus Enum**:
```java
public enum DeliveryStatus {
    PENDING,  // 발송 대기
    SENT,     // 발송 완료
    FAILED,   // 발송 실패
    READ      // 읽음
}
```

---

## 📝 중요 설계 원칙

### 아키텍처 원칙

#### 1. 계층별 책임 분리 (Layered Architecture)

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │  ← Controller (REST API)
│         (web.controller)                │
└──────────────────┬──────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────┐
│         Application Layer               │  ← Service (비즈니스 로직)
│         (service)                       │
└──────────────────┬──────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────┐
│         Infrastructure Layer            │  ← Repository (데이터 접근)
│         (repository)                    │
└──────────────────┬──────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────┐
│         Domain Layer                    │  ← Entity, Enum (순수 비즈니스)
│         (domain)                        │
└─────────────────────────────────────────┘
```

**규칙**:
- ✅ 상위 계층이 하위 계층에 의존 (단방향)
- ❌ 하위 계층이 상위 계층에 의존 금지
- ✅ Domain은 어떤 계층에도 의존하지 않음 (순수성 유지)

#### 2. Domain 순수성 (Domain Purity)

**Domain 계층의 책임**:
- 비즈니스 엔티티 정의
- 비즈니스 규칙 (validation, 상태 변경)
- Value Object, Enum

**Domain이 가져서는 안 되는 것**:
- ❌ Repository 참조
- ❌ Service 참조  
- ❌ Controller 참조
- ❌ 외부 라이브러리 의존성 (JPA 제외)

```java
// ✅ Good: 순수한 Domain 로직
public class User extends SoftDeletableEntity {
    
    public void verifyEmail() {
        if (this.deletedAt != null) {
            throw new IllegalStateException("Cannot verify deleted user");
        }
        this.primaryEmailVerified = true;
    }
    
    public boolean canCreatePortfolio(int currentCount) {
        return currentCount < 10; // 비즈니스 규칙
    }
}

// ❌ Bad: Repository를 Domain에서 참조
public class User {
    @Autowired
    private UserRepository userRepository; // 절대 금지!
}
```

#### 3. Repository 패턴

**Repository의 책임**:
- 데이터 접근 추상화
- CRUD 메서드 제공
- 커스텀 쿼리 (필요시)

```java
@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    
    // 단순 조회
    Optional<User> findByPrimaryEmail(String email);
    
    // Soft Delete 고려
    Optional<User> findByUserIdAndDeletedAtIsNull(UUID userId);
    List<User> findAllByDeletedAtIsNull();
    
    // 존재 확인
    boolean existsByPrimaryEmailAndDeletedAtIsNull(String email);
    
    // 커스텀 쿼리
    @Query("SELECT u FROM User u WHERE u.status = :status AND u.deletedAt IS NULL")
    List<User> findActiveUsers(@Param("status") UserStatus status);
}
```

#### 4. Service 패턴

**Service의 책임**:
- 비즈니스 로직 조합
- 트랜잭션 관리
- 여러 Repository 조합
- Domain 객체 생성/수정

```java
@Service
@Transactional(readOnly = true)
public class PortfolioService {
    
    private final PortfolioRepository portfolioRepository;
    private final PositionRepository positionRepository;
    private final AssetRepository assetRepository;
    
    // Constructor injection (권장)
    public PortfolioService(
        PortfolioRepository portfolioRepository,
        PositionRepository positionRepository,
        AssetRepository assetRepository
    ) {
        this.portfolioRepository = portfolioRepository;
        this.positionRepository = positionRepository;
        this.assetRepository = assetRepository;
    }
    
    @Transactional
    public Portfolio createPortfolio(UUID userId, String name) {
        // 1. 비즈니스 규칙 검증
        long portfolioCount = portfolioRepository.countByUserIdAndDeletedAtIsNull(userId);
        if (portfolioCount >= 10) {
            throw new BusinessException("Maximum portfolio limit reached");
        }
        
        // 2. Domain 객체 생성
        Portfolio portfolio = new Portfolio();
        portfolio.setUserId(userId);
        portfolio.setPortfolioName(name);
        
        // 3. 저장
        return portfolioRepository.save(portfolio);
    }
    
    @Transactional
    public void addPosition(UUID portfolioId, UUID assetId, BigDecimal quantity) {
        // 여러 Repository 조합
        Portfolio portfolio = portfolioRepository.findById(portfolioId)
            .orElseThrow(() -> new NotFoundException("Portfolio not found"));
        
        Asset asset = assetRepository.findById(assetId)
            .orElseThrow(() -> new NotFoundException("Asset not found"));
        
        Position position = new Position();
        position.setPortfolio(portfolio);
        position.setAsset(asset);
        position.setQuantity(quantity);
        
        positionRepository.save(position);
    }
}
```

### 코딩 컨벤션

### 1. Soft Delete 패턴
- `users`, `portfolios`, `positions` 테이블에 `deletedAt` 필드 사용
- 데이터 복구 및 이력 추적 가능

### 2. Audit 필드
- 모든 주요 테이블에 `createdAt`, `updatedAt` 포함
- Spring Data JPA의 `@CreatedDate`, `@LastModifiedDate` 활용

### 3. UUID 사용
- 모든 PK는 UUID 타입 사용 (보안, 분산 환경 대비)

### 4. Enum 타입
- 상태값은 가능한 한 Enum으로 관리
- `@Enumerated(EnumType.STRING)` 사용 (DB에 문자열 저장)

### 5. JSONB 활용
- PostgreSQL의 JSONB 타입 활용 (유연한 데이터 저장)
- `tags`, `metadata`, `parsedData` 등

### 6. 제약조건
- 비즈니스 로직 레벨의 중복 방지를 DB 레벨에서도 보장
- `@UniqueConstraint` 적극 활용

### 7. 인덱스 전략
- 조회 패턴에 맞는 복합 인덱스 설계
- 정렬이 필요한 컬럼에 DESC 인덱스 고려

---

## 🔧 Spring Data JPA 구현 가이드

### BaseEntity 클래스

**위치**: `com.portrally.domain.common.BaseEntity`

```java
package com.portrally.domain.common;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Column;
import javax.persistence.EntityListeners;
import javax.persistence.MappedSuperclass;
import java.time.Instant;

@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity {
    
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @LastModifiedDate
    @Column(name = "updated_at")
    private Instant updatedAt;
    
    // Getters
    public Instant getCreatedAt() {
        return createdAt;
    }
    
    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
```

### SoftDeletableEntity 클래스

**위치**: `com.portrally.domain.common.SoftDeletableEntity`

```java
package com.portrally.domain.common;

import javax.persistence.Column;
import javax.persistence.MappedSuperclass;
import java.time.Instant;

@MappedSuperclass
public abstract class SoftDeletableEntity extends BaseEntity {
    
    @Column(name = "deleted_at")
    private Instant deletedAt;
    
    public boolean isDeleted() {
        return deletedAt != null;
    }
    
    public void softDelete() {
        this.deletedAt = Instant.now();
    }
    
    public void restore() {
        this.deletedAt = null;
    }
    
    // Getter
    public Instant getDeletedAt() {
        return deletedAt;
    }
}
```

### Repository 예시

**위치**: `com.portrally.repository.user.UserRepository`

```java
package com.portrally.repository.user;

import com.portrally.domain.user.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    
    Optional<User> findByPrimaryEmail(String email);
    
    Optional<User> findByUserIdAndDeletedAtIsNull(UUID userId);
    
    boolean existsByPrimaryEmail(String email);
}
```

### Service 예시

**위치**: `com.portrally.service.user.UserService`

```java
package com.portrally.service.user;

import com.portrally.domain.user.User;
import com.portrally.repository.user.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@Transactional(readOnly = true)
public class UserService {
    
    private final UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    @Transactional
    public User createUser(String email, String displayName) {
        User user = new User();
        user.setPrimaryEmail(email);
        user.setDisplayName(displayName);
        return userRepository.save(user);
    }
    
    public User findById(UUID userId) {
        return userRepository.findByUserIdAndDeletedAtIsNull(userId)
            .orElseThrow(() -> new IllegalArgumentException("User not found"));
    }
}
```

### 패키지 구조 제안

> **Clean Architecture 원칙에 따른 계층별 분리**

```
com.portrally
├── domain                          # 도메인 계층 (비즈니스 로직)
│   ├── user
│   │   ├── User.java
│   │   ├── SocialAccount.java
│   │   ├── UserPreference.java
│   │   ├── UserStatus.java        # enum
│   │   ├── SocialProvider.java    # enum
│   │   └── RiskTolerance.java     # enum
│   │
│   ├── portfolio
│   │   ├── Portfolio.java
│   │   ├── PortfolioMetric.java
│   │   ├── PortfolioAiInsight.java
│   │   ├── Position.java
│   │   ├── InsightStatus.java     # enum
│   │   └── SourceType.java        # enum
│   │
│   ├── asset
│   │   ├── Asset.java
│   │   ├── AssetMetric.java
│   │   ├── AssetAiInsight.java
│   │   ├── AssetType.java         # enum
│   │   └── Recommendation.java    # enum
│   │
│   ├── ocr
│   │   ├── UploadedImage.java
│   │   ├── OcrResult.java
│   │   ├── OcrDetectedPosition.java
│   │   ├── UploadStatus.java      # enum
│   │   └── OcrStatus.java         # enum
│   │
│   ├── news
│   │   ├── NewsArticle.java
│   │   └── NewsAssetRelation.java
│   │
│   ├── notification
│   │   ├── NotificationType.java
│   │   ├── UserNotificationSetting.java
│   │   ├── NotificationLog.java
│   │   ├── NotificationCategory.java    # enum
│   │   ├── NotificationPriority.java    # enum
│   │   ├── DeliveryChannel.java         # enum
│   │   └── DeliveryStatus.java          # enum
│   │
│   ├── audit
│   │   └── AuditLog.java
│   │
│   └── common                      # 공통 도메인 요소
│       ├── BaseEntity.java
│       └── SoftDeletableEntity.java
│
├── repository                      # 데이터 접근 계층
│   ├── user
│   │   ├── UserRepository.java
│   │   ├── SocialAccountRepository.java
│   │   └── UserPreferenceRepository.java
│   │
│   ├── portfolio
│   │   ├── PortfolioRepository.java
│   │   ├── PortfolioMetricRepository.java
│   │   ├── PortfolioAiInsightRepository.java
│   │   └── PositionRepository.java
│   │
│   ├── asset
│   │   ├── AssetRepository.java
│   │   ├── AssetMetricRepository.java
│   │   └── AssetAiInsightRepository.java
│   │
│   ├── ocr
│   │   ├── UploadedImageRepository.java
│   │   ├── OcrResultRepository.java
│   │   └── OcrDetectedPositionRepository.java
│   │
│   ├── news
│   │   ├── NewsArticleRepository.java
│   │   └── NewsAssetRelationRepository.java
│   │
│   ├── notification
│   │   ├── NotificationTypeRepository.java
│   │   ├── UserNotificationSettingRepository.java
│   │   └── NotificationLogRepository.java
│   │
│   └── audit
│       └── AuditLogRepository.java
│
├── service                         # 비즈니스 로직 계층
│   ├── user
│   │   └── UserService.java
│   ├── portfolio
│   │   └── PortfolioService.java
│   └── asset
│       └── AssetService.java
│
└── web                            # 프레젠테이션 계층
    └── controller
        ├── UserController.java
        ├── PortfolioController.java
        └── AssetController.java
```

#### 패키지 구조 설계 원칙

**1. 계층별 분리 (Layered Architecture)**
- `domain`: 비즈니스 로직과 엔티티 (다른 계층에 의존하지 않음)
- `repository`: 데이터 접근 (domain에 의존)
- `service`: 비즈니스 로직 조합 (domain + repository 사용)
- `web`: API 엔드포인트 (service 사용)

**2. 의존성 방향**
```
web → service → repository → domain
                              ↑
                      (다른 계층이 의존)
```

**3. Domain 순수성 유지**
- Domain 엔티티는 JPA 애노테이션만 포함
- Repository, Service, Controller에 대한 의존성 없음
- 순수한 Java 객체로 단위 테스트 가능

**4. Enum 위치**
- 각 도메인 패키지 내에 관련 enum 배치
- 도메인 로직과 강하게 결합된 타입들

---

## ✅ 체크리스트

### 필수 수정사항
- [ ] `positions` 테이블에 `deletedAt` 필드 추가
- [ ] `portfolio_metrics`에 `UNIQUE(portfolio_id, snapshot_date)` 제약 추가
- [ ] `user_notification_settings`에 `UNIQUE(user_id, notification_type_id)` 제약 추가

### 구현 순서 제안

#### Phase 1: 기반 구조 (Foundation)
1. **Common Layer**
   - `BaseEntity`, `SoftDeletableEntity` 작성
   - JPA Auditing 설정

2. **User Domain**
   - Domain: `User`, `SocialAccount`, `UserPreference` + Enums
   - Repository: `UserRepository`, `SocialAccountRepository`
   - Service: `UserService` (기본 CRUD)

#### Phase 2: 핵심 도메인 (Core Domain)
3. **Asset Domain**
   - Domain: `Asset`, `AssetType`
   - Repository: `AssetRepository`
   - Service: `AssetService`

4. **Portfolio Domain**
   - Domain: `Portfolio`, `Position`, `SourceType`
   - Repository: `PortfolioRepository`, `PositionRepository`
   - Service: `PortfolioService`

#### Phase 3: OCR 워크플로우
5. **OCR Domain**
   - Domain: `UploadedImage`, `OcrResult`, `OcrDetectedPosition` + Enums
   - Repository: 각각의 Repository
   - Service: `OcrService`

#### Phase 4: AI 분석 (Analytics)
6. **AI Insights**
   - Domain: `PortfolioAiInsight`, `AssetAiInsight`, `PortfolioMetric`, `AssetMetric`
   - Repository: 각각의 Repository
   - Service: `AiInsightService`, `MetricService`

#### Phase 5: 알림 시스템 (Notification)
7. **Notification Domain**
   - Domain: `NotificationType`, `UserNotificationSetting`, `NotificationLog` + Enums
   - Repository: 각각의 Repository
   - Service: `NotificationService`

#### Phase 6: 부가 기능 (Additional Features)
8. **News & Audit**
   - Domain: `NewsArticle`, `NewsAssetRelation`, `AuditLog`
   - Repository: 각각의 Repository
   - Service: `NewsService`, `AuditService`

#### 각 Phase별 작업 순서
```
1. Domain 엔티티 작성 (+ Enum)
   ↓
2. Repository 인터페이스 작성
   ↓
3. Service 작성 (비즈니스 로직)
   ↓
4. 단위 테스트 (Domain)
   ↓
5. 통합 테스트 (Repository)
   ↓
6. Controller 작성 (API)
   ↓
7. E2E 테스트
```

---

## 📚 참고사항

### PostgreSQL 타입 매핑
- `UUID` → `java.util.UUID`
- `TIMESTAMPTZ` → `java.time.Instant`
- `DATE` → `java.time.LocalDate`
- `TIME` → `java.time.LocalTime`
- `NUMERIC(28,8)` → `java.math.BigDecimal`
- `JSONB` → `String` (JPA Converter 사용 시 Map/Object 가능)

### 권장 라이브러리
- Spring Data JPA
- Hibernate (JPA 구현체)
- Flyway or Liquibase (DB 마이그레이션)
- QueryDSL (타입 안전 쿼리)
- MapStruct (DTO 매핑)
