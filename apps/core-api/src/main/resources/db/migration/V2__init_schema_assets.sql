-- =============================================
-- V2: Assets (Securities) & News Domain
-- =============================================

-- 1. Assets Master Table
CREATE TABLE IF NOT EXISTS assets_master (
    asset_id BIGSERIAL PRIMARY KEY,
    national TEXT NOT NULL,           -- KR, US, HK, JP, CN, VN
    market TEXT NOT NULL,             -- KOSPI, KOSDAQ, NAS, NYS, HKS, AMS
    symbol TEXT NOT NULL,             -- 단축코드 / Symbol
    isin TEXT NULL,                   -- KR... / (없으면 NULL)
    name_ko TEXT NULL,
    name_en TEXT NULL,
    asset_type VARCHAR(32) NULL,      -- STOCK, ETF, etc.
    currency TEXT NOT NULL,           -- KRW, USD...
    sector_scheme TEXT NULL,          -- optional but recommended
    sector_tags TEXT[] NULL,          -- ['Technology', 'Semiconductor']
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_assets_master UNIQUE (national, market, symbol),
    CONSTRAINT assets_master_asset_type_chk CHECK (asset_type IN ('STOCK', 'ETF', 'ETN', 'INDEX', 'WARRANT', 'CRYPTO', 'BOND', 'CASH', 'OTHER'))
);

CREATE INDEX IF NOT EXISTS idx_assets_master_symbol ON assets_master(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_master_market ON assets_master(market);
CREATE INDEX IF NOT EXISTS idx_assets_master_national ON assets_master(national);
CREATE INDEX IF NOT EXISTS idx_assets_master_name_ko ON assets_master(name_ko);
CREATE INDEX IF NOT EXISTS idx_assets_master_name_en ON assets_master(name_en);

-- 2. Asset AI Insights Table
CREATE TABLE IF NOT EXISTS asset_ai_insights (
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
    CONSTRAINT uk_asset_insight_type_date UNIQUE (asset_id, insight_type, analysis_date),
    CONSTRAINT asset_ai_insights_recommendation_chk CHECK (recommendation IN ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL')),
    CONSTRAINT asset_ai_insights_status_chk CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'ARCHIVED'))
);

CREATE INDEX IF NOT EXISTS idx_asset_ai_insights_asset_date ON asset_ai_insights(asset_id, analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_asset_ai_insights_type_date ON asset_ai_insights(insight_type, analysis_date DESC);

-- 3. Assets Metrics Table
CREATE TABLE IF NOT EXISTS assets_metrics (
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

-- 4. News Articles Table
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

-- 5. News Asset Relations Table
CREATE TABLE news_asset_relations (
    news_asset_relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    news_id BIGINT NOT NULL REFERENCES news_articles(news_id) ON DELETE CASCADE,
    asset_id BIGINT NOT NULL REFERENCES assets_master(asset_id) ON DELETE CASCADE,
    relevance_score NUMERIC(5,4),
    CONSTRAINT uk_news_asset UNIQUE (news_id, asset_id)
);

CREATE INDEX idx_news_asset_relations_news_id ON news_asset_relations(news_id);
CREATE INDEX idx_news_asset_relations_asset_id ON news_asset_relations(asset_id);
