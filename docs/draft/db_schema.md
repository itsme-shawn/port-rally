# PortRally Database Schema

> **Database**: PostgreSQL 16
> **ORM**: Spring Data R2DBC
> **Migration**: Flyway
> **총 테이블**: 19개

2026.01.03

---

## 1. User Domain

### 1.1 users

사용자 계정 정보

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    display_name VARCHAR(100),
    primary_email VARCHAR(255),
    primary_email_verified BOOLEAN NOT NULL DEFAULT false,
    profile_image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    signup_completed_at TIMESTAMPTZ,
    terms_accepted_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT users_status_chk CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'DELETED'))
);

CREATE UNIQUE INDEX uk_users_primary_email ON users(primary_email) WHERE primary_email IS NOT NULL;
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
```

```java
@Table("users")
public class User {
    @Id
    private UUID userId;
    private UserStatus status;
    private String displayName;
    private String primaryEmail;
    private Boolean primaryEmailVerified;
    private String profileImageUrl;
    private Instant createdAt;
    private Instant updatedAt;
    private Instant lastLoginAt;
    private Instant signupCompletedAt;
    private Instant termsAcceptedAt;
    private Instant deletedAt;
}
```

### 1.2 social_accounts

소셜 로그인 연동 정보

```sql
CREATE TABLE social_accounts (
    social_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    provider_email_verified BOOLEAN,
    scopes TEXT,
    linked_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT social_accounts_provider_chk CHECK (provider IN ('GOOGLE', 'KAKAO', 'NAVER', 'APPLE')),
    CONSTRAINT uk_social_provider_user_id UNIQUE (provider, provider_user_id),
    CONSTRAINT uk_user_provider UNIQUE (user_id, provider)
);

CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);
```

```java
@Table("social_accounts")
public class SocialAccount {
    @Id
    private UUID socialAccountId;
    private UUID userId;
    private SocialProvider provider;
    private String providerUserId;
    private String providerEmail;
    private Boolean providerEmailVerified;
    private String scopes;
    private Instant linkedAt;
    private Instant lastLoginAt;
    private Boolean isActive;
    private Instant revokedAt;
}
```

### 1.3 user_preferences

사용자 개인 설정 (User와 1:1)

```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    notification_enabled BOOLEAN NOT NULL DEFAULT true,
    dark_mode BOOLEAN NOT NULL DEFAULT false,
    risk_tolerance VARCHAR(32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT user_preferences_risk_tolerance_chk
        CHECK (risk_tolerance IS NULL OR risk_tolerance IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE'))
);
```

```java
@Table("user_preferences")
public class UserPreference {
    @Id
    private UUID userId;
    private Boolean notificationEnabled;
    private Boolean darkMode;
    private RiskTolerance riskTolerance;
    private Instant createdAt;
    private Instant updatedAt;
}
```

---

## 2. Portfolio Domain

### 2.1 portfolios

사용자의 포트폴리오

```sql
CREATE TABLE portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(100) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    base_currency VARCHAR(10) NOT NULL DEFAULT 'KRW',
    investment_type VARCHAR(50),
    goal VARCHAR(50),
    sector_focus VARCHAR(100),
    tags JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_user_deleted ON portfolios(user_id, deleted_at);
```

```java
@Table("portfolios")
public class Portfolio {
    @Id
    private UUID portfolioId;
    private UUID userId;
    private String portfolioName;
    private Boolean isPrimary;
    private String baseCurrency;
    private String investmentType;
    private String goal;
    private String sectorFocus;
    private String tags;  // JSONB as String
    private Instant createdAt;
    private Instant updatedAt;
    private Instant deletedAt;
}
```

### 2.2 positions

포트폴리오별 종목 보유 현황

```sql
CREATE TABLE positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets_master(asset_id) ON DELETE RESTRICT,
    quantity NUMERIC(28,8) NOT NULL,
    average_cost NUMERIC(28,8),
    cost_basis NUMERIC(28,8),
    source_type VARCHAR(32),
    value NUMERIC(28,8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT positions_source_type_chk CHECK (source_type IN ('MANUAL', 'OCR'))
);

CREATE INDEX idx_positions_portfolio_asset ON positions(portfolio_id, asset_id);
CREATE INDEX idx_positions_portfolio_deleted ON positions(portfolio_id, deleted_at);
```

```java
@Table("positions")
public class Position {
    @Id
    private UUID positionId;
    private UUID portfolioId;
    private UUID assetId;
    private BigDecimal quantity;
    private BigDecimal averageCost;
    private BigDecimal costBasis;
    private SourceType sourceType;
    private BigDecimal value;
    private Instant createdAt;
    private Instant updatedAt;
    private Instant deletedAt;
}
```

### 2.3 portfolio_metrics

포트폴리오 일별 성과 지표

```sql
CREATE TABLE portfolio_metrics (
    portfolio_metrics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_value NUMERIC(28,8),
    total_cost NUMERIC(28,8),
    total_pnl NUMERIC(28,8),
    total_pnl_percent NUMERIC(10,4),
    daily_pnl_percent NUMERIC(10,4),
    weekly_pnl_percent NUMERIC(10,4),
    monthly_pnl_percent NUMERIC(10,4),
    ytd_pnl_percent NUMERIC(10,4),
    volatility NUMERIC(10,6),
    sharpe_ratio NUMERIC(10,6),
    max_drawdown NUMERIC(10,6),
    var_95 NUMERIC(28,8),
    beta NUMERIC(10,6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_portfolio_metrics_date UNIQUE (portfolio_id, snapshot_date)
);

CREATE INDEX idx_portfolio_metrics_portfolio_date ON portfolio_metrics(portfolio_id, snapshot_date DESC);
```

```java
@Table("portfolio_metrics")
public class PortfolioMetric {
    @Id
    private UUID portfolioMetricsId;
    private UUID portfolioId;
    private LocalDate snapshotDate;
    private BigDecimal totalValue;
    private BigDecimal totalCost;
    private BigDecimal totalPnl;
    private BigDecimal totalPnlPercent;
    private BigDecimal dailyPnlPercent;
    private BigDecimal weeklyPnlPercent;
    private BigDecimal monthlyPnlPercent;
    private BigDecimal ytdPnlPercent;
    private BigDecimal volatility;
    private BigDecimal sharpeRatio;
    private BigDecimal maxDrawdown;
    private BigDecimal var95;
    private BigDecimal beta;
    private Instant createdAt;
}
```

### 2.4 portfolio_ai_insights

포트폴리오 AI 분석 (개인별)

```sql
CREATE TABLE portfolio_ai_insights (
    portfolio_insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,
    title VARCHAR(200) NOT NULL,
    executive_summary TEXT,
    full_report TEXT NOT NULL,
    health_score NUMERIC(5,4),
    risk_score NUMERIC(5,4),
    diversification_score NUMERIC(5,4),
    performance_score NUMERIC(5,4),
    generated_by VARCHAR(50),
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMPTZ,
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT portfolio_ai_insights_status_chk CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'ARCHIVED')),
    CONSTRAINT uk_portfolio_insight_type_date UNIQUE (portfolio_id, insight_type, analysis_date)
);

CREATE INDEX idx_portfolio_ai_insights_user_date ON portfolio_ai_insights(user_id, analysis_date DESC);
CREATE INDEX idx_portfolio_ai_insights_portfolio_type ON portfolio_ai_insights(portfolio_id, insight_type, analysis_date DESC);
CREATE INDEX idx_portfolio_ai_insights_user_read ON portfolio_ai_insights(user_id, is_read, created_at DESC);
CREATE INDEX idx_portfolio_ai_insights_status ON portfolio_ai_insights(status, generated_at DESC);
```

```java
@Table("portfolio_ai_insights")
public class PortfolioAiInsight {
    @Id
    private UUID portfolioInsightId;
    private UUID userId;
    private UUID portfolioId;
    private String insightType;
    private LocalDate analysisDate;
    private String title;
    private String executiveSummary;
    private String fullReport;
    private BigDecimal healthScore;
    private BigDecimal riskScore;
    private BigDecimal diversificationScore;
    private BigDecimal performanceScore;
    private String generatedBy;
    private Integer version;
    private InsightStatus status;
    private Boolean isRead;
    private Instant readAt;
    private Instant generatedAt;
    private Instant createdAt;
    private Instant updatedAt;
}
```

---

## 3. Asset Domain

### 3.1 assets_master

자산 마스터 정보

```sql
CREATE TABLE assets_master (
    asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    asset_type VARCHAR(32) NOT NULL,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(10),
    currency VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT assets_master_asset_type_chk CHECK (asset_type IN ('STOCK', 'ETF', 'CRYPTO', 'BOND', 'CASH')),
    CONSTRAINT uk_asset_market_symbol_type UNIQUE (market, symbol, asset_type)
);

CREATE INDEX idx_assets_master_symbol ON assets_master(symbol);
CREATE INDEX idx_assets_master_market ON assets_master(market);
CREATE INDEX idx_assets_master_is_active ON assets_master(is_active);
```

```java
@Table("assets_master")
public class Asset {
    @Id
    private UUID assetId;
    private String symbol;
    private String market;
    private AssetType assetType;
    private String name;
    private String sector;
    private String industry;
    private String country;
    private String currency;
    private Boolean isActive;
    private Instant createdAt;
    private Instant updatedAt;
}
```

### 3.2 asset_ai_insights

종목별 AI 분석 (전체 사용자 공용)

```sql
CREATE TABLE asset_ai_insights (
    asset_insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets_master(asset_id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content TEXT NOT NULL,
    sentiment_score NUMERIC(5,4),
    technical_score NUMERIC(5,4),
    fundamental_score NUMERIC(5,4),
    overall_score NUMERIC(5,4),
    recommendation VARCHAR(32),
    confidence_level NUMERIC(5,4),
    price_at_analysis NUMERIC(28,8),
    target_price NUMERIC(28,8),
    support_price NUMERIC(28,8),
    resistance_price NUMERIC(28,8),
    key_factors TEXT,
    risk_factors TEXT,
    generated_by VARCHAR(50),
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    view_count INTEGER NOT NULL DEFAULT 0,
    generated_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT asset_ai_insights_recommendation_chk
        CHECK (recommendation IN ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL')),
    CONSTRAINT asset_ai_insights_status_chk CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'ARCHIVED')),
    CONSTRAINT uk_asset_insight_type_date UNIQUE (asset_id, insight_type, analysis_date)
);

CREATE INDEX idx_asset_ai_insights_asset_date ON asset_ai_insights(asset_id, analysis_date DESC);
CREATE INDEX idx_asset_ai_insights_type_date ON asset_ai_insights(insight_type, analysis_date DESC);
CREATE INDEX idx_asset_ai_insights_recommendation ON asset_ai_insights(recommendation, analysis_date DESC);
CREATE INDEX idx_asset_ai_insights_status ON asset_ai_insights(status, generated_at DESC);
```

```java
@Table("asset_ai_insights")
public class AssetAiInsight {
    @Id
    private UUID assetInsightId;
    private UUID assetId;
    private String insightType;
    private LocalDate analysisDate;
    private String title;
    private String summary;
    private String content;
    private BigDecimal sentimentScore;
    private BigDecimal technicalScore;
    private BigDecimal fundamentalScore;
    private BigDecimal overallScore;
    private Recommendation recommendation;
    private BigDecimal confidenceLevel;
    private BigDecimal priceAtAnalysis;
    private BigDecimal targetPrice;
    private BigDecimal supportPrice;
    private BigDecimal resistancePrice;
    private String keyFactors;
    private String riskFactors;
    private String generatedBy;
    private Integer version;
    private InsightStatus status;
    private Integer viewCount;
    private Instant generatedAt;
    private Instant expiresAt;
    private Instant createdAt;
    private Instant updatedAt;
}
```

### 3.3 assets_metrics

종목별 기술적 지표

```sql
CREATE TABLE assets_metrics (
    indicator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_insight_id UUID NOT NULL REFERENCES asset_ai_insights(asset_insight_id) ON DELETE CASCADE,
    rsi_14 NUMERIC(10,4),
    macd_value NUMERIC(28,8),
    macd_signal NUMERIC(28,8),
    ma_20 NUMERIC(28,8),
    ma_50 NUMERIC(28,8),
    ma_200 NUMERIC(28,8),
    bollinger_upper NUMERIC(28,8),
    bollinger_middle NUMERIC(28,8),
    bollinger_lower NUMERIC(28,8),
    volume_avg_20 BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assets_metrics_insight_id ON assets_metrics(asset_insight_id);
```

```java
@Table("assets_metrics")
public class AssetMetric {
    @Id
    private UUID indicatorId;
    private UUID assetInsightId;
    private BigDecimal rsi14;
    private BigDecimal macdValue;
    private BigDecimal macdSignal;
    private BigDecimal ma20;
    private BigDecimal ma50;
    private BigDecimal ma200;
    private BigDecimal bollingerUpper;
    private BigDecimal bollingerMiddle;
    private BigDecimal bollingerLower;
    private Long volumeAvg20;
    private Instant createdAt;
}
```

---

## 4. OCR Domain

### 4.1 uploaded_images

사용자가 업로드한 계좌 이미지

```sql
CREATE TABLE uploaded_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    storage_url TEXT NOT NULL,
    upload_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    content_type VARCHAR(100),
    file_size BIGINT,
    hash_sha256 CHAR(64),
    retention_policy VARCHAR(50) NOT NULL DEFAULT '90_DAYS',
    retain_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uploaded_images_upload_status_chk
        CHECK (upload_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'))
);

CREATE INDEX idx_uploaded_images_user_id ON uploaded_images(user_id);
CREATE INDEX idx_uploaded_images_portfolio_id ON uploaded_images(portfolio_id);
CREATE INDEX idx_uploaded_images_status ON uploaded_images(upload_status);
CREATE INDEX idx_uploaded_images_hash ON uploaded_images(hash_sha256);
```

```java
@Table("uploaded_images")
public class UploadedImage {
    @Id
    private UUID imageId;
    private UUID userId;
    private UUID portfolioId;
    private String storageUrl;
    private UploadStatus uploadStatus;
    private String contentType;
    private Long fileSize;
    private String hashSha256;
    private String retentionPolicy;
    private Instant retainUntil;
    private Instant createdAt;
}
```

### 4.2 ocr_results

AI OCR 결과

```sql
CREATE TABLE ocr_results (
    ocr_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL UNIQUE REFERENCES uploaded_images(image_id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    raw_text TEXT,
    parsed_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT ocr_results_status_chk CHECK (status IN ('PENDING', 'VERIFIED', 'REJECTED', 'FAILED'))
);

CREATE INDEX idx_ocr_results_status ON ocr_results(status);
```

```java
@Table("ocr_results")
public class OcrResult {
    @Id
    private UUID ocrResultId;
    private UUID imageId;
    private OcrStatus status;
    private String rawText;
    private String parsedData;  // JSONB as String
    private Instant createdAt;
    private Instant updatedAt;
}
```

### 4.3 ocr_detected_positions

OCR로 감지된 종목 정보

```sql
CREATE TABLE ocr_detected_positions (
    ocr_detected_position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ocr_result_id UUID NOT NULL REFERENCES ocr_results(ocr_result_id) ON DELETE CASCADE,
    detected_symbol VARCHAR(50),
    detected_name VARCHAR(255),
    detected_market VARCHAR(50),
    quantity NUMERIC(28,8),
    average_cost NUMERIC(28,8),
    match_asset_id UUID REFERENCES assets_master(asset_id) ON DELETE SET NULL,
    match_confidence NUMERIC(5,4),
    is_confirmed BOOLEAN NOT NULL DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ocr_detected_positions_ocr_result ON ocr_detected_positions(ocr_result_id);
CREATE INDEX idx_ocr_detected_positions_match_asset ON ocr_detected_positions(match_asset_id);
CREATE INDEX idx_ocr_detected_positions_confirmed ON ocr_detected_positions(is_confirmed);
```

```java
@Table("ocr_detected_positions")
public class OcrDetectedPosition {
    @Id
    private UUID ocrDetectedPositionId;
    private UUID ocrResultId;
    private String detectedSymbol;
    private String detectedName;
    private String detectedMarket;
    private BigDecimal quantity;
    private BigDecimal averageCost;
    private UUID matchAssetId;
    private BigDecimal matchConfidence;
    private Boolean isConfirmed;
    private Instant confirmedAt;
    private Instant createdAt;
}
```

---

## 5. News Domain

### 5.1 news_articles

뉴스 기사

```sql
CREATE TABLE news_articles (
    news_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL,
    source_url TEXT UNIQUE,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC(5,4),
    impact_score NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_news_articles_published_at ON news_articles(published_at DESC);
CREATE INDEX idx_news_articles_source ON news_articles(source);
CREATE INDEX idx_news_articles_sentiment ON news_articles(sentiment_score);
```

```java
@Table("news_articles")
public class NewsArticle {
    @Id
    private UUID newsId;
    private String source;
    private String sourceUrl;
    private String title;
    private String content;
    private String summary;
    private Instant publishedAt;
    private BigDecimal sentimentScore;
    private BigDecimal impactScore;
    private Instant createdAt;
}
```

### 5.2 news_asset_relations

뉴스-종목 연결 (N:N)

```sql
CREATE TABLE news_asset_relations (
    news_asset_relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    news_id UUID NOT NULL REFERENCES news_articles(news_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets_master(asset_id) ON DELETE CASCADE,
    relevance_score NUMERIC(5,4),
    CONSTRAINT uk_news_asset UNIQUE (news_id, asset_id)
);

CREATE INDEX idx_news_asset_relations_news_id ON news_asset_relations(news_id);
CREATE INDEX idx_news_asset_relations_asset_id ON news_asset_relations(asset_id);
```

```java
@Table("news_asset_relations")
public class NewsAssetRelation {
    @Id
    private UUID newsAssetRelationId;
    private UUID newsId;
    private UUID assetId;
    private BigDecimal relevanceScore;
}
```

---

## 6. Notification Domain

### 6.1 notification_types

알림 종류 정의 (마스터)

```sql
CREATE TABLE notification_types (
    notification_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(32) NOT NULL,
    description TEXT,
    default_enabled BOOLEAN NOT NULL DEFAULT true,
    default_channels VARCHAR(200) NOT NULL DEFAULT 'PUSH,IN_APP',
    is_user_configurable BOOLEAN NOT NULL DEFAULT true,
    priority VARCHAR(32) NOT NULL DEFAULT 'NORMAL',
    icon VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT notification_types_category_chk CHECK (category IN ('AI', 'MARKET', 'SYSTEM')),
    CONSTRAINT notification_types_priority_chk CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT'))
);

CREATE INDEX idx_notification_types_category ON notification_types(category, is_active);
```

```java
@Table("notification_types")
public class NotificationType {
    @Id
    private UUID notificationTypeId;
    private String typeName;
    private NotificationCategory category;
    private String description;
    private Boolean defaultEnabled;
    private String defaultChannels;
    private Boolean isUserConfigurable;
    private NotificationPriority priority;
    private String icon;
    private Boolean isActive;
    private Instant createdAt;
    private Instant updatedAt;
}
```

### 6.2 user_notification_settings

사용자별 알림 설정

```sql
CREATE TABLE user_notification_settings (
    settings_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type_id UUID NOT NULL REFERENCES notification_types(notification_type_id) ON DELETE CASCADE,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    delivery_channels VARCHAR(200) NOT NULL DEFAULT 'PUSH,IN_APP',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    preferred_time TIME,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT uk_user_notification_type UNIQUE (user_id, notification_type_id)
);

CREATE INDEX idx_user_notification_settings_user ON user_notification_settings(user_id, is_enabled);
```

```java
@Table("user_notification_settings")
public class UserNotificationSetting {
    @Id
    private UUID settingsId;
    private UUID userId;
    private UUID notificationTypeId;
    private Boolean isEnabled;
    private String deliveryChannels;
    private LocalTime quietHoursStart;
    private LocalTime quietHoursEnd;
    private LocalTime preferredTime;
    private Instant createdAt;
    private Instant updatedAt;
}
```

### 6.3 notifications_logs

알림 발송 기록

```sql
CREATE TABLE notifications_logs (
    notification_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type_id UUID NOT NULL REFERENCES notification_types(notification_type_id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    delivery_channel VARCHAR(32) NOT NULL,
    delivery_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    priority VARCHAR(32) NOT NULL DEFAULT 'NORMAL',
    source_type VARCHAR(50),
    source_id UUID,
    related_portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    related_asset_id UUID REFERENCES assets_master(asset_id) ON DELETE SET NULL,
    action_url TEXT,
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    failed_reason TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT notifications_logs_delivery_channel_chk CHECK (delivery_channel IN ('PUSH', 'EMAIL', 'SMS', 'IN_APP')),
    CONSTRAINT notifications_logs_delivery_status_chk CHECK (delivery_status IN ('PENDING', 'SENT', 'FAILED', 'READ')),
    CONSTRAINT notifications_logs_priority_chk CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT'))
);

CREATE INDEX idx_notifications_logs_user_read ON notifications_logs(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_logs_user_type ON notifications_logs(user_id, notification_type_id, created_at DESC);
CREATE INDEX idx_notifications_logs_type_created ON notifications_logs(notification_type_id, created_at DESC);
CREATE INDEX idx_notifications_logs_status ON notifications_logs(delivery_status, created_at);
CREATE INDEX idx_notifications_logs_source ON notifications_logs(source_type, source_id);
```

```java
@Table("notifications_logs")
public class NotificationLog {
    @Id
    private UUID notificationLogId;
    private UUID userId;
    private UUID notificationTypeId;
    private String title;
    private String message;
    private DeliveryChannel deliveryChannel;
    private DeliveryStatus deliveryStatus;
    private NotificationPriority priority;
    private String sourceType;
    private UUID sourceId;
    private UUID relatedPortfolioId;
    private UUID relatedAssetId;
    private String actionUrl;
    private Boolean isRead;
    private Instant readAt;
    private Instant sentAt;
    private String failedReason;
    private Integer retryCount;
    private Instant createdAt;
}
```

---

## 7. Audit Domain

### 7.1 audit_logs

사용자 활동 감사 로그

```sql
CREATE TABLE audit_logs (
    audit_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

```java
@Table("audit_logs")
public class AuditLog {
    @Id
    private UUID auditLogId;
    private UUID userId;
    private String eventType;
    private String metadata;  // JSONB as String
    private Instant createdAt;
}
```

---

## 8. Enum Types

모든 ENUM은 V8 마이그레이션에서 `VARCHAR(32) + CHECK`로 변환됨.

| Enum | Values |
|------|--------|
| `UserStatus` | PENDING, ACTIVE, SUSPENDED, DELETED |
| `SocialProvider` | GOOGLE, KAKAO, NAVER, APPLE |
| `RiskTolerance` | CONSERVATIVE, MODERATE, AGGRESSIVE |
| `AssetType` | STOCK, ETF, CRYPTO, BOND, CASH |
| `Recommendation` | STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL |
| `InsightStatus` | ACTIVE, SUPERSEDED, ARCHIVED |
| `SourceType` | MANUAL, OCR |
| `UploadStatus` | PENDING, PROCESSING, COMPLETED, FAILED |
| `OcrStatus` | PENDING, VERIFIED, REJECTED, FAILED |
| `NotificationCategory` | AI, MARKET, SYSTEM |
| `NotificationPriority` | LOW, NORMAL, HIGH, URGENT |
| `DeliveryChannel` | PUSH, EMAIL, SMS, IN_APP |
| `DeliveryStatus` | PENDING, SENT, FAILED, READ |

---

## 9. ER Diagram (Text)

```
users (1) ──┬── (N) social_accounts
            ├── (1) user_preferences
            ├── (N) portfolios ──┬── (N) positions ── assets_master
            │                    ├── (N) portfolio_metrics
            │                    └── (N) portfolio_ai_insights
            ├── (N) uploaded_images ── (1) ocr_results ── (N) ocr_detected_positions
            ├── (N) user_notification_settings
            ├── (N) notifications_logs
            └── (N) audit_logs

assets_master (1) ──┬── (N) asset_ai_insights ── (1) assets_metrics
                    ├── (N) positions
                    └── (N) news_asset_relations ── news_articles

notification_types (1) ──┬── (N) user_notification_settings
                         └── (N) notifications_logs
```
