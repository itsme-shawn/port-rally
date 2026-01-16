-- =============================================
-- V3: Portfolio & Position Domain
-- =============================================

-- 1. Portfolios Table
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

-- 2. Positions Table (With all recent additions)
CREATE TABLE positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id BIGINT NOT NULL REFERENCES assets_master(asset_id) ON DELETE RESTRICT,
    quantity NUMERIC(28,8) NOT NULL,
    average_cost NUMERIC(28,8),
    cost_basis NUMERIC(28,8),
    source_type VARCHAR(32),
    value NUMERIC(28,8) NOT NULL,
    
    -- Additional columns from V11
    currency VARCHAR(10) NOT NULL DEFAULT 'KRW',
    purchase_date DATE,
    broker VARCHAR(50),
    account_alias VARCHAR(100),
    
    -- V15: Position Value (explicit column if needed, though 'value' exists above, V15 added position_value specifically?)
    -- Note: V3 original had 'value', V15 added 'position_value'. Let's check if 'value' was total value.
    -- Assuming 'value' in V3 was current market value, V15 might have been redundant or clarified.
    -- Let's stick to the latest schema: V15 added 'position_value'.
    -- If 'value' already existed in V3 script, then V15 might be adding a different field or V3 script I read was pre-V15?
    -- Looking at cat output: V3 had `value NUMERIC(28,8) NOT NULL`. V15 `ADD COLUMN position_value`.
    -- This implies duplication or different meaning. I will include `position_value` as well to be safe, or assume `value` is enough.
    -- Let's add `position_value` to match V15 exactly.
    position_value NUMERIC(28,8),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,

    CONSTRAINT positions_source_type_chk CHECK (source_type IN ('MANUAL', 'OCR'))
);

-- Unique constraint from V13
CREATE UNIQUE INDEX uk_positions_portfolio_asset ON positions (portfolio_id, asset_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_positions_portfolio_asset ON positions(portfolio_id, asset_id);
CREATE INDEX idx_positions_portfolio_deleted ON positions(portfolio_id, deleted_at);

-- 3. Portfolio Metrics Table
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

-- 4. Portfolio AI Insights Table
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
    CONSTRAINT uk_portfolio_insight_type_date UNIQUE (portfolio_id, insight_type, analysis_date),
    CONSTRAINT portfolio_ai_insights_status_chk CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'ARCHIVED'))
);

CREATE INDEX idx_portfolio_ai_insights_user_date ON portfolio_ai_insights(user_id, analysis_date DESC);
