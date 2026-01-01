-- =============================================
-- V2: Asset/Stock Tables
-- =============================================

-- Enum Types for Asset domain
CREATE TYPE asset_type AS ENUM ('STOCK', 'ETF', 'CRYPTO', 'BOND', 'CASH');
CREATE TYPE recommendation AS ENUM ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL');
CREATE TYPE insight_status AS ENUM ('ACTIVE', 'SUPERSEDED', 'ARCHIVED');

-- =============================================
-- 3.1 assets_master
-- =============================================
CREATE TABLE assets_master (
    asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    asset_type asset_type NOT NULL,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(10),
    currency VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT uk_asset_market_symbol_type UNIQUE (market, symbol, asset_type)
);

CREATE INDEX idx_assets_master_symbol ON assets_master(symbol);
CREATE INDEX idx_assets_master_market ON assets_master(market);
CREATE INDEX idx_assets_master_is_active ON assets_master(is_active);

COMMENT ON TABLE assets_master IS '투자 가능한 모든 자산의 마스터 정보';
COMMENT ON COLUMN assets_master.symbol IS '티커/심볼';
COMMENT ON COLUMN assets_master.market IS 'KRX, NASDAQ, NYSE, etc.';
COMMENT ON COLUMN assets_master.asset_type IS 'stock, etf, crypto, bond, cash';

-- =============================================
-- 3.3 asset_ai_insights
-- =============================================
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
    recommendation recommendation,
    confidence_level NUMERIC(5,4),
    price_at_analysis NUMERIC(28,8),
    target_price NUMERIC(28,8),
    support_price NUMERIC(28,8),
    resistance_price NUMERIC(28,8),
    key_factors TEXT,
    risk_factors TEXT,
    generated_by VARCHAR(50),
    version INTEGER NOT NULL DEFAULT 1,
    status insight_status NOT NULL DEFAULT 'ACTIVE',
    view_count INTEGER NOT NULL DEFAULT 0,
    generated_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT uk_asset_insight_type_date UNIQUE (asset_id, insight_type, analysis_date)
);

CREATE INDEX idx_asset_ai_insights_asset_date ON asset_ai_insights(asset_id, analysis_date DESC);
CREATE INDEX idx_asset_ai_insights_type_date ON asset_ai_insights(insight_type, analysis_date DESC);
CREATE INDEX idx_asset_ai_insights_recommendation ON asset_ai_insights(recommendation, analysis_date DESC);
CREATE INDEX idx_asset_ai_insights_status ON asset_ai_insights(status, generated_at DESC);

COMMENT ON TABLE asset_ai_insights IS '종목별 AI 분석 (전체 사용자 공용)';
COMMENT ON COLUMN asset_ai_insights.insight_type IS 'daily_summary, technical_analysis, etc.';
COMMENT ON COLUMN asset_ai_insights.sentiment_score IS '감성 점수 (-1~1)';
COMMENT ON COLUMN asset_ai_insights.recommendation IS '매매 추천';

-- =============================================
-- 3.2 assets_metrics
-- =============================================
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

COMMENT ON TABLE assets_metrics IS '종목별 기술적 지표';
COMMENT ON COLUMN assets_metrics.rsi_14 IS 'RSI (14일)';
COMMENT ON COLUMN assets_metrics.macd_value IS 'MACD 값';
COMMENT ON COLUMN assets_metrics.ma_20 IS '20일 이동평균';
