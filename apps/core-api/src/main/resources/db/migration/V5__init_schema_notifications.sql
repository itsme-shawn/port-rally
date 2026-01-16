-- =============================================
-- V5: Notification Domain
-- =============================================

-- 1. Notification Types Table
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

-- 2. User Notification Settings Table
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

-- 3. Notifications Logs Table
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
