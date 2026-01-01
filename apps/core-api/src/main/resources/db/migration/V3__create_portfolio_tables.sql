-- =============================================
-- V3: Portfolio Tables
-- =============================================

-- Enum Types for Portfolio domain
CREATE TYPE source_type AS ENUM ('MANUAL', 'OCR');

-- =============================================
-- 2.1 portfolios
-- =============================================
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

COMMENT ON TABLE portfolios IS '사용자의 포트폴리오';
COMMENT ON COLUMN portfolios.is_primary IS '대표 포트폴리오 여부';
COMMENT ON COLUMN portfolios.base_currency IS '기준 통화 (KRW, USD)';
COMMENT ON COLUMN portfolios.tags IS '태그 (JSONB)';

-- =============================================
-- 4.1 positions
-- =============================================
CREATE TABLE positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets_master(asset_id) ON DELETE RESTRICT,
    quantity NUMERIC(28,8) NOT NULL,
    average_cost NUMERIC(28,8),
    cost_basis NUMERIC(28,8),
    source_type source_type,
    value NUMERIC(28,8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_positions_portfolio_asset ON positions(portfolio_id, asset_id);
CREATE INDEX idx_positions_portfolio_deleted ON positions(portfolio_id, deleted_at);

COMMENT ON TABLE positions IS '포트폴리오별 종목 보유 현황';
COMMENT ON COLUMN positions.quantity IS '보유 수량';
COMMENT ON COLUMN positions.average_cost IS '평균 단가';
COMMENT ON COLUMN positions.cost_basis IS '총 매입원가';
COMMENT ON COLUMN positions.source_type IS 'MANUAL, OCR';

-- =============================================
-- 2.2 portfolio_metrics
-- =============================================
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

COMMENT ON TABLE portfolio_metrics IS '포트폴리오의 일별 성과 추적 및 지표';
COMMENT ON COLUMN portfolio_metrics.total_pnl_percent IS '총 수익률 (%)';
COMMENT ON COLUMN portfolio_metrics.sharpe_ratio IS '샤프 지수';
COMMENT ON COLUMN portfolio_metrics.max_drawdown IS '최대 낙폭 (%)';
COMMENT ON COLUMN portfolio_metrics.var_95 IS 'VaR (95%)';

-- =============================================
-- 2.3 portfolio_ai_insights
-- =============================================
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
    status insight_status NOT NULL DEFAULT 'ACTIVE',
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMPTZ,
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT uk_portfolio_insight_type_date UNIQUE (portfolio_id, insight_type, analysis_date)
);

CREATE INDEX idx_portfolio_ai_insights_user_date ON portfolio_ai_insights(user_id, analysis_date DESC);
CREATE INDEX idx_portfolio_ai_insights_portfolio_type ON portfolio_ai_insights(portfolio_id, insight_type, analysis_date DESC);
CREATE INDEX idx_portfolio_ai_insights_user_read ON portfolio_ai_insights(user_id, is_read, created_at DESC);
CREATE INDEX idx_portfolio_ai_insights_status ON portfolio_ai_insights(status, generated_at DESC);

COMMENT ON TABLE portfolio_ai_insights IS '포트폴리오 종합 AI 분석 (개인별)';
COMMENT ON COLUMN portfolio_ai_insights.insight_type IS 'daily_report, weekly_review, etc.';
COMMENT ON COLUMN portfolio_ai_insights.health_score IS '포트폴리오 건강도 (0~1)';
COMMENT ON COLUMN portfolio_ai_insights.diversification_score IS '분산도 점수 (0~1)';
