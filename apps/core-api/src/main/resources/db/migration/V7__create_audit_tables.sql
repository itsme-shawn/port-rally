-- =============================================
-- V7: Audit Tables
-- =============================================

-- =============================================
-- 1.4 audit_logs
-- =============================================
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

COMMENT ON TABLE audit_logs IS '사용자 활동 감사 로그';
COMMENT ON COLUMN audit_logs.event_type IS '이벤트 타입: LOGIN, LINK_SOCIAL, PORTFOLIO_CREATE, IMAGE_UPLOAD, POSITION_ADD, etc.';
COMMENT ON COLUMN audit_logs.metadata IS '메타데이터 (JSON)';
