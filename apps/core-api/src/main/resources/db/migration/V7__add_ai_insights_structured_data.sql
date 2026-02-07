-- =============================================
-- V7: Add Structured AI Insights Data
-- =============================================
-- Purpose: Extend portfolio_ai_insights table to store structured analysis data
-- for better frontend consumption

-- Add JSONB columns for structured AI analysis data
ALTER TABLE portfolio_ai_insights
ADD COLUMN IF NOT EXISTS insights_data JSONB,
ADD COLUMN IF NOT EXISTS recommendations_data JSONB,
ADD COLUMN IF NOT EXISTS sectors_data JSONB,
ADD COLUMN IF NOT EXISTS risk_metrics JSONB;

-- Add indexes for JSONB columns for better query performance
CREATE INDEX IF NOT EXISTS idx_portfolio_ai_insights_insights_data 
ON portfolio_ai_insights USING GIN (insights_data);

CREATE INDEX IF NOT EXISTS idx_portfolio_ai_insights_recommendations_data 
ON portfolio_ai_insights USING GIN (recommendations_data);

-- Add comments for documentation
COMMENT ON COLUMN portfolio_ai_insights.insights_data IS 
'Structured insights array: [{type, title, description, impact}]';

COMMENT ON COLUMN portfolio_ai_insights.recommendations_data IS 
'Structured recommendations array: [{action, title, description, priority}]';

COMMENT ON COLUMN portfolio_ai_insights.sectors_data IS 
'Sector distribution array: [{name, percentage, color}]';

COMMENT ON COLUMN portfolio_ai_insights.risk_metrics IS 
'Detailed risk metrics: {volatility, sharpe_ratio, beta, max_drawdown, level}';
