-- =============================================
-- V6: Notification Tables
-- =============================================

-- Enum Types for Notification domain
CREATE TYPE notification_category AS ENUM ('AI', 'MARKET', 'SYSTEM');
CREATE TYPE notification_priority AS ENUM ('LOW', 'NORMAL', 'HIGH', 'URGENT');
CREATE TYPE delivery_channel AS ENUM ('PUSH', 'EMAIL', 'SMS', 'IN_APP');
CREATE TYPE delivery_status AS ENUM ('PENDING', 'SENT', 'FAILED', 'READ');

-- =============================================
-- 7.1 notification_types
-- =============================================
CREATE TABLE notification_types (
    notification_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE,
    category notification_category NOT NULL,
    description TEXT,
    default_enabled BOOLEAN NOT NULL DEFAULT true,
    default_channels VARCHAR(200) NOT NULL DEFAULT 'PUSH,IN_APP',
    is_user_configurable BOOLEAN NOT NULL DEFAULT true,
    priority notification_priority NOT NULL DEFAULT 'NORMAL',
    icon VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_notification_types_category ON notification_types(category, is_active);

COMMENT ON TABLE notification_types IS '시스템에서 제공하는 알림 종류 정의 (마스터 데이터)';
COMMENT ON COLUMN notification_types.type_name IS '알림 타입명';
COMMENT ON COLUMN notification_types.category IS 'ai, market, system';
COMMENT ON COLUMN notification_types.default_channels IS '기본 채널 (push,email)';
COMMENT ON COLUMN notification_types.is_user_configurable IS '사용자 설정 가능 여부';

-- =============================================
-- 7.2 user_notification_settings
-- =============================================
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

COMMENT ON TABLE user_notification_settings IS '사용자별 알림 수신 설정';
COMMENT ON COLUMN user_notification_settings.delivery_channels IS '수신 채널 (push,email,sms)';
COMMENT ON COLUMN user_notification_settings.quiet_hours_start IS '방해금지 시작';
COMMENT ON COLUMN user_notification_settings.quiet_hours_end IS '방해금지 종료';

-- =============================================
-- 7.3 notifications_logs
-- =============================================
CREATE TABLE notifications_logs (
    notification_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type_id BIGINT NOT NULL REFERENCES notification_types(notification_type_id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    delivery_channel delivery_channel NOT NULL,
    delivery_status delivery_status NOT NULL DEFAULT 'PENDING',
    priority notification_priority NOT NULL DEFAULT 'NORMAL',
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_logs_user_read ON notifications_logs(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_logs_user_type ON notifications_logs(user_id, notification_type_id, created_at DESC);
CREATE INDEX idx_notifications_logs_type_created ON notifications_logs(notification_type_id, created_at DESC);
CREATE INDEX idx_notifications_logs_status ON notifications_logs(delivery_status, created_at);
CREATE INDEX idx_notifications_logs_source ON notifications_logs(source_type, source_id);

COMMENT ON TABLE notifications_logs IS '실제 발송된 알림의 기록 및 상태 관리';
COMMENT ON COLUMN notifications_logs.source_type IS '출처 타입';
COMMENT ON COLUMN notifications_logs.source_id IS '출처 레코드 ID (다형성)';
COMMENT ON COLUMN notifications_logs.action_url IS '클릭 URL/딥링크';
COMMENT ON COLUMN notifications_logs.retry_count IS '재시도 횟수';
