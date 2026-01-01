-- =============================================
-- V8: Convert PostgreSQL ENUM types to VARCHAR + CHECK
-- R2DBC 호환성 개선을 위해 DB ENUM 타입을 VARCHAR로 변환
-- =============================================

-- 1) users.status
ALTER TABLE users
    ALTER COLUMN status TYPE VARCHAR(32) USING status::text;
ALTER TABLE users
    ADD CONSTRAINT users_status_chk
    CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'DELETED'));

-- 2) social_accounts.provider
ALTER TABLE social_accounts
    ALTER COLUMN provider TYPE VARCHAR(32) USING provider::text;
ALTER TABLE social_accounts
    ADD CONSTRAINT social_accounts_provider_chk
    CHECK (provider IN ('GOOGLE', 'KAKAO', 'NAVER', 'APPLE'));

-- 3) user_preferences.risk_tolerance (nullable)
ALTER TABLE user_preferences
    ALTER COLUMN risk_tolerance TYPE VARCHAR(32) USING risk_tolerance::text;
ALTER TABLE user_preferences
    ADD CONSTRAINT user_preferences_risk_tolerance_chk
    CHECK (risk_tolerance IS NULL OR risk_tolerance IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE'));

-- 4) assets_master.asset_type
ALTER TABLE assets_master
    ALTER COLUMN asset_type TYPE VARCHAR(32) USING asset_type::text;
ALTER TABLE assets_master
    ADD CONSTRAINT assets_master_asset_type_chk
    CHECK (asset_type IN ('STOCK', 'ETF', 'CRYPTO', 'BOND', 'CASH'));

-- 5) asset_ai_insights.recommendation
ALTER TABLE asset_ai_insights
    ALTER COLUMN recommendation TYPE VARCHAR(32) USING recommendation::text;
ALTER TABLE asset_ai_insights
    ADD CONSTRAINT asset_ai_insights_recommendation_chk
    CHECK (recommendation IN ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'));

-- 6) asset_ai_insights.status
ALTER TABLE asset_ai_insights
    ALTER COLUMN status TYPE VARCHAR(32) USING status::text;
ALTER TABLE asset_ai_insights
    ADD CONSTRAINT asset_ai_insights_status_chk
    CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'ARCHIVED'));

-- 7) portfolio_ai_insights.status
ALTER TABLE portfolio_ai_insights
    ALTER COLUMN status TYPE VARCHAR(32) USING status::text;
ALTER TABLE portfolio_ai_insights
    ADD CONSTRAINT portfolio_ai_insights_status_chk
    CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'ARCHIVED'));

-- 8) positions.source_type
ALTER TABLE positions
    ALTER COLUMN source_type TYPE VARCHAR(32) USING source_type::text;
ALTER TABLE positions
    ADD CONSTRAINT positions_source_type_chk
    CHECK (source_type IN ('MANUAL', 'OCR'));

-- 9) uploaded_images.upload_status
ALTER TABLE uploaded_images
    ALTER COLUMN upload_status TYPE VARCHAR(32) USING upload_status::text;
ALTER TABLE uploaded_images
    ADD CONSTRAINT uploaded_images_upload_status_chk
    CHECK (upload_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'));

-- 10) ocr_results.status
ALTER TABLE ocr_results
    ALTER COLUMN status TYPE VARCHAR(32) USING status::text;
ALTER TABLE ocr_results
    ADD CONSTRAINT ocr_results_status_chk
    CHECK (status IN ('PENDING', 'VERIFIED', 'REJECTED', 'FAILED'));

-- 11) notification_types.category
ALTER TABLE notification_types
    ALTER COLUMN category TYPE VARCHAR(32) USING category::text;
ALTER TABLE notification_types
    ADD CONSTRAINT notification_types_category_chk
    CHECK (category IN ('AI', 'MARKET', 'SYSTEM'));

-- 12) notification_types.priority
ALTER TABLE notification_types
    ALTER COLUMN priority TYPE VARCHAR(32) USING priority::text;
ALTER TABLE notification_types
    ADD CONSTRAINT notification_types_priority_chk
    CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT'));

-- 13) notifications_logs.delivery_channel
ALTER TABLE notifications_logs
    ALTER COLUMN delivery_channel TYPE VARCHAR(32) USING delivery_channel::text;
ALTER TABLE notifications_logs
    ADD CONSTRAINT notifications_logs_delivery_channel_chk
    CHECK (delivery_channel IN ('PUSH', 'EMAIL', 'SMS', 'IN_APP'));

-- 14) notifications_logs.delivery_status
ALTER TABLE notifications_logs
    ALTER COLUMN delivery_status TYPE VARCHAR(32) USING delivery_status::text;
ALTER TABLE notifications_logs
    ADD CONSTRAINT notifications_logs_delivery_status_chk
    CHECK (delivery_status IN ('PENDING', 'SENT', 'FAILED', 'READ'));

-- 15) notifications_logs.priority
ALTER TABLE notifications_logs
    ALTER COLUMN priority TYPE VARCHAR(32) USING priority::text;
ALTER TABLE notifications_logs
    ADD CONSTRAINT notifications_logs_priority_chk
    CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT'));

-- Drop old ENUM types (optional, but keeps schema clean)
DROP TYPE IF EXISTS user_status CASCADE;
DROP TYPE IF EXISTS social_provider CASCADE;
DROP TYPE IF EXISTS risk_tolerance CASCADE;
DROP TYPE IF EXISTS asset_type CASCADE;
DROP TYPE IF EXISTS recommendation CASCADE;
DROP TYPE IF EXISTS insight_status CASCADE;
DROP TYPE IF EXISTS source_type CASCADE;
DROP TYPE IF EXISTS upload_status CASCADE;
DROP TYPE IF EXISTS ocr_status CASCADE;
DROP TYPE IF EXISTS notification_category CASCADE;
DROP TYPE IF EXISTS notification_priority CASCADE;
DROP TYPE IF EXISTS delivery_channel CASCADE;
DROP TYPE IF EXISTS delivery_status CASCADE;
