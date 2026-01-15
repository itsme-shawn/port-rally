# PortRally Database Schema

> 버전: v0.2.0
> 최종 수정일: 2026-01-15
> Database: PostgreSQL 16
> ORM: Spring Data R2DBC
> Migration: Flyway
> 총 테이블: 22개 (User, Portfolio, Asset, OCR, News, Notification, Audit, Terms domains)

## 개정 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-15 | v0.2.0 | 마이그레이션 파일(V1~V13) 기반 스키마 동기화 (Terms 도메인 추가, Positions 컬럼 추가, 제약조건 업데이트) |
| 2026-01-15 | v0.1.0 | 문서 버전 관리 추가 |
| 2026-01-04 | v0.0.0 | 초기 작성 (V8 ENUM → VARCHAR 변환 반영) |

---

## 목차

1. [User Domain](#1-user-domain)
2. [Portfolio Domain](#2-portfolio-domain)
3. [Asset Domain](#3-asset-domain)
4. [OCR Domain](#4-ocr-domain)
5. [News Domain](#5-news-domain)
6. [Notification Domain](#6-notification-domain)
7. [Audit Domain](#7-audit-domain)
8. [Market Data Domain](#8-market-data-domain)
9. [Terms Domain](#9-terms-domain)
10. [Enum Types](#10-enum-types)
11. [ER Diagram](#11-er-diagram)
12. [히스토리](#12-히스토리)

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

-- V10: 탈퇴한 유저는 중복 체크에서 제외
CREATE UNIQUE INDEX uk_users_primary_email ON users(primary_email) WHERE primary_email IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
```

```java
@Table("users")
public class User {
    @Id
    private UUID userId;
    private String status; // Checked via constraint
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
    CONSTRAINT social_accounts_provider_chk CHECK (provider IN ('GOOGLE', 'KAKAO', 'NAVER', 'APPLE'))
);

-- V10: 해지된 연동은 중복 체크에서 제외
CREATE UNIQUE INDEX uk_social_provider_user_id ON social_accounts(provider, provider_user_id) WHERE revoked_at IS NULL AND is_active = true;
CREATE UNIQUE INDEX uk_user_provider ON social_accounts(user_id, provider) WHERE revoked_at IS NULL AND is_active = true;
CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);
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

---

## 2. Portfolio Domain

### 2.1 portfolios

사용자의 포트폴리오

```sql
CREATE TABLE portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(100) NOT NULL,
    description TEXT,
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

### 2.2 positions

포트폴리오별 종목 보유 현황

```sql
CREATE TABLE positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id BIGINT NOT NULL REFERENCES assets_master(asset_id) ON DELETE RESTRICT,
    quantity NUMERIC(28,8) NOT NULL,
    average_cost NUMERIC(28,8),
    cost_basis NUMERIC(28,8),
    source_type VARCHAR(32),
    value NUMERIC(28,8) NOT NULL,
    position_value NUMERIC(28,8),
    currency VARCHAR(10) NOT NULL DEFAULT 'KRW', -- V11 added
    purchase_date DATE,                        -- V11 added
    broker VARCHAR(50),                        -- V11 added
    account_alias VARCHAR(100),                -- V11 added
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT positions_source_type_chk CHECK (source_type IN ('MANUAL', 'OCR'))
);

CREATE INDEX idx_positions_portfolio_asset ON positions(portfolio_id, asset_id);
CREATE INDEX idx_positions_portfolio_deleted ON positions(portfolio_id, deleted_at);
-- V13: 한 포트폴리오 내 동일 종목 중복 방지 (삭제되지 않은 것 중)
CREATE UNIQUE INDEX uk_positions_portfolio_asset ON positions (portfolio_id, asset_id) WHERE deleted_at IS NULL;
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

---

## 3. Asset Domain

### 3.1 assets_master

자산 마스터 정보 (securities_master 기반 통합 테이블)

```sql
CREATE TABLE assets_master (
    asset_id BIGSERIAL PRIMARY KEY,
    national TEXT NOT NULL,           -- KR, US, HK, JP, CN, VN
    market TEXT NOT NULL,             -- KOSPI, KOSDAQ, NAS, NYS, HKS, AMS
    symbol TEXT NOT NULL,             -- 단축코드 / Symbol
    isin TEXT NULL,                   -- KR... / (없으면 NULL)
    name_ko TEXT NULL,
    name_en TEXT NULL,
    asset_type VARCHAR(32) NULL,      -- STOCK/ETF/ETN/INDEX/WARRANT/CRYPTO/BOND/CASH/OTHER
    currency TEXT NOT NULL,           -- KRW/USD...
    sector_scheme TEXT NULL,          -- optional but recommended
    sector_tags TEXT[] NULL,          -- ['Technology', 'Semiconductor', 'Memory']
    is_active BOOLEAN NOT NULL DEFAULT true, -- (Note: V2 sql doesn't explicitly show is_active default in some versions, but implied)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assets_master_asset_type_chk CHECK (asset_type IN ('STOCK', 'ETF', 'ETN', 'INDEX', 'WARRANT', 'CRYPTO', 'BOND', 'CASH', 'OTHER')),
    CONSTRAINT uq_assets_master UNIQUE (national, market, symbol)
);

CREATE INDEX idx_assets_master_symbol ON assets_master(symbol);
CREATE INDEX idx_assets_master_market ON assets_master(market);
CREATE INDEX idx_assets_master_national ON assets_master(national);
CREATE INDEX idx_assets_master_isin ON assets_master(isin);
CREATE INDEX idx_assets_master_name_ko ON assets_master(name_ko);
CREATE INDEX idx_assets_master_name_en ON assets_master(name_en);
```

```java
@Table("assets_master")
public class Asset {
    @Id
    private Long assetId;
    private String national;
    private String market;
    private String symbol;
    private String assetType; // Checked via constraint
    private String nameKo;
    private String nameEn;
    private String currency;
    private String sectorScheme;
    private String[] sectorTags;
    private Instant createdAt;
    private Instant updatedAt;
}
```

### 3.2 asset_ai_insights

종목별 AI 분석 (전체 사용자 공용)

```sql
CREATE TABLE asset_ai_insights (
    asset_insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id BIGINT NOT NULL REFERENCES assets_master(asset_id) ON DELETE CASCADE,
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
    match_asset_id BIGINT REFERENCES assets_master(asset_id) ON DELETE SET NULL,
    is_confirmed BOOLEAN NOT NULL DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    currency VARCHAR(10) NOT NULL DEFAULT 'KRW',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ocr_detected_positions_ocr_result ON ocr_detected_positions(ocr_result_id);
CREATE INDEX idx_ocr_detected_positions_match_asset ON ocr_detected_positions(match_asset_id);
CREATE INDEX idx_ocr_detected_positions_confirmed ON ocr_detected_positions(is_confirmed);
```

---

## 5. News Domain

### 5.1 news_articles

뉴스 기사

```sql
CREATE TABLE news_articles (
    news_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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

### 5.2 news_asset_relations

뉴스-종목 연결 (N:N)

```sql
CREATE TABLE news_asset_relations (
    news_asset_relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    news_id BIGINT NOT NULL REFERENCES news_articles(news_id) ON DELETE CASCADE,
    asset_id BIGINT NOT NULL REFERENCES assets_master(asset_id) ON DELETE CASCADE,
    relevance_score NUMERIC(5,4),
    CONSTRAINT uk_news_asset UNIQUE (news_id, asset_id)
);

CREATE INDEX idx_news_asset_relations_news_id ON news_asset_relations(news_id);
CREATE INDEX idx_news_asset_relations_asset_id ON news_asset_relations(asset_id);
```

---

## 6. Notification Domain

### 6.1 notification_types

알림 종류 정의 (마스터)

```sql
CREATE TABLE notification_types (
    notification_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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

### 6.2 user_notification_settings

사용자별 알림 설정

```sql
CREATE TABLE user_notification_settings (
    settings_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type_id BIGINT NOT NULL REFERENCES notification_types(notification_type_id) ON DELETE CASCADE,
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

### 6.3 notifications_logs

알림 발송 기록

```sql
CREATE TABLE notifications_logs (
    notification_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type_id BIGINT NOT NULL REFERENCES notification_types(notification_type_id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    delivery_channel VARCHAR(32) NOT NULL,
    delivery_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    priority VARCHAR(32) NOT NULL DEFAULT 'NORMAL',
    source_type VARCHAR(50),
    source_id UUID,
    related_portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    related_asset_id BIGINT REFERENCES assets_master(asset_id) ON DELETE SET NULL,
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

---

## 7. Audit Domain

### 7.1 audit_logs

사용자 활동 감사 로그

```sql
CREATE TABLE audit_logs (
    audit_log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

## 8. Market Data Domain

### 8.1 Market Data Pipeline & assets_master

Market Data 서비스는 외부 제공자(KIS, Upbit 등)로부터 수집된 데이터를 `assets_master` 테이블(Section 3.1 참조)에 적재합니다.

*   **주요 역할**: 전 세계 마켓(KOSPI, KOSDAQ, NAS, NYS, HKS, AMS 등)의 종목 마스터 정보 통합
*   **데이터 흐름**: `Daily CSV Crawling` -> `Master Loader` -> `assets_master` Table Upsert
*   **관리 대상**:
    *   Symbol, Name (Ko/En), ISIN
    *   Asset Type (Stock, ETF, Crypto, etc.)
    *   Sector / Industry Tags

(과거 `securities_master`로 불렸으나 현재 `assets_master`로 통합됨)

---

## 9. Terms Domain

### 9.1 terms

서비스 약관 정보

```sql
CREATE TABLE terms (
    terms_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    terms_type VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT terms_type_chk CHECK (terms_type IN ('SERVICE', 'PRIVACY', 'MARKETING', 'LOCATION', 'THIRD_PARTY')),
    CONSTRAINT uk_terms_type UNIQUE (terms_type)
);

CREATE INDEX idx_terms_type ON terms(terms_type);
CREATE INDEX idx_terms_is_active ON terms(is_active);
CREATE INDEX idx_terms_display_order ON terms(display_order);
```

### 9.2 user_terms_agreements

사용자 약관 동의 이력

```sql
CREATE TABLE user_terms_agreements (
    agreement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    terms_id BIGINT NOT NULL REFERENCES terms(terms_id) ON DELETE CASCADE,
    agreed BOOLEAN NOT NULL DEFAULT true,
    agreed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    CONSTRAINT uk_user_terms UNIQUE (user_id, terms_id)
);

CREATE INDEX idx_user_terms_agreements_user_id ON user_terms_agreements(user_id);
CREATE INDEX idx_user_terms_agreements_terms_id ON user_terms_agreements(terms_id);
CREATE INDEX idx_user_terms_agreements_agreed_at ON user_terms_agreements(agreed_at);
```

---

## 10. Enum Types

모든 ENUM은 V8 마이그레이션에서 `VARCHAR(32) + CHECK`로 변환됨.

| Enum | Values |
|------|--------|
| `UserStatus` | PENDING, ACTIVE, SUSPENDED, DELETED |
| `SocialProvider` | GOOGLE, KAKAO, NAVER, APPLE |
| `RiskTolerance` | CONSERVATIVE, MODERATE, AGGRESSIVE |
| `AssetType` | STOCK, ETF, ETN, INDEX, WARRANT, CRYPTO, BOND, CASH, OTHER |
| `Recommendation` | STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL |
| `InsightStatus` | ACTIVE, SUPERSEDED, ARCHIVED |
| `SourceType` | MANUAL, OCR |
| `UploadStatus` | PENDING, PROCESSING, COMPLETED, FAILED |
| `OcrStatus` | PENDING, VERIFIED, REJECTED, FAILED |
| `NotificationCategory` | AI, MARKET, SYSTEM |
| `NotificationPriority` | LOW, NORMAL, HIGH, URGENT |
| `DeliveryChannel` | PUSH, EMAIL, SMS, IN_APP |
| `DeliveryStatus` | PENDING, SENT, FAILED, READ |
| `TermsType` | SERVICE, PRIVACY, MARKETING, LOCATION, THIRD_PARTY |

---

## 11. ER Diagram

```
users (1) ──┬── (N) social_accounts
            ├── (1) user_preferences
            ├── (N) portfolios ──┬── (N) positions ── assets_master
            │                    ├── (N) portfolio_metrics
            │                    └── (N) portfolio_ai_insights
            ├── (N) uploaded_images ── (1) ocr_results ── (N) ocr_detected_positions
            ├── (N) user_notification_settings
            ├── (N) notifications_logs
            ├── (N) audit_logs
            └── (N) user_terms_agreements ── (1) terms

assets_master (1) ──┬── (N) asset_ai_insights ── (1) assets_metrics
                    ├── (N) positions
                    └── (N) news_asset_relations ── news_articles

notification_types (1) ──┬── (N) user_notification_settings
                         └── (N) notifications_logs
```

---

## 12. 히스토리

### 12.1 JPA → R2DBC 전환 (2026-01-03)

(생략 - 기존 내용 유지)

### 12.2 securities_master 테이블 설계 변경

#### v1.0 (초기 설계) - Deprecated

(생략 - 기존 내용 유지)

#### v2.0 (현재)

**변경 사항**: `securities_master`를 `assets_master`로 통합 및 확장. ISIN, Sector Tags, Asset Type 확장 등을 통해 다양한 자산군을 수용하도록 설계됨.

---

## 부록 A. 관련 문서

- [Market Data Pipeline](./marketdata_pipeline.md) - 시세 수집 아키텍처
- [Active Symbol](./active_symbol.md) - 동적 심볼 관리
- [Spring Boot R2DBC](./springboot_r2dbc.md) - Core API 구현

---

## 부록 B. PostgreSQL 타입 매핑

| PostgreSQL | Java |
|-----------|------|
| `UUID` | `java.util.UUID` |
| `TIMESTAMPTZ` | `java.time.Instant` |
| `DATE` | `java.time.LocalDate` |
| `TIME` | `java.time.LocalTime` |
| `NUMERIC(28,8)` | `java.math.BigDecimal` |
| `JSONB` | `String` (JPA Converter 사용 시 Map/Object 가능) |
| `TEXT[]` | `String[]` |