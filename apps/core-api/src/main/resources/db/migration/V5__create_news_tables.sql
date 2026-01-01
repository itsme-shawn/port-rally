-- =============================================
-- V5: News Tables
-- =============================================

-- =============================================
-- 6.1 news_articles
-- =============================================
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

COMMENT ON TABLE news_articles IS '뉴스 기사 저장';
COMMENT ON COLUMN news_articles.source IS '출처';
COMMENT ON COLUMN news_articles.source_url IS '원문 URL (중복 방지)';
COMMENT ON COLUMN news_articles.sentiment_score IS '감성 점수 (-1~1)';
COMMENT ON COLUMN news_articles.impact_score IS '영향력 점수 (0~1)';

-- =============================================
-- 6.2 news_asset_relations
-- =============================================
CREATE TABLE news_asset_relations (
    news_asset_relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    news_id UUID NOT NULL REFERENCES news_articles(news_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets_master(asset_id) ON DELETE CASCADE,
    relevance_score NUMERIC(5,4),
    CONSTRAINT uk_news_asset UNIQUE (news_id, asset_id)
);

CREATE INDEX idx_news_asset_relations_news_id ON news_asset_relations(news_id);
CREATE INDEX idx_news_asset_relations_asset_id ON news_asset_relations(asset_id);

COMMENT ON TABLE news_asset_relations IS '뉴스와 종목의 연결 테이블 (N:N)';
COMMENT ON COLUMN news_asset_relations.relevance_score IS '연관도 점수 (0~1)';
