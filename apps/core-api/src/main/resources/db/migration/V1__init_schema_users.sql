-- =============================================
-- V1: User, Auth, Audit, Terms Domain
-- =============================================

-- 1. Users Table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    display_name VARCHAR(100),
    primary_email VARCHAR(255),
    primary_email_verified BOOLEAN NOT NULL DEFAULT false,
    profile_image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    signup_completed_at TIMESTAMPTZ,
    terms_accepted_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT users_status_chk CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'DELETED'))
);

-- Unique index for non-null emails
CREATE UNIQUE INDEX uk_users_primary_email ON users(primary_email) WHERE primary_email IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status);

-- 2. Social Accounts Table
CREATE TABLE social_accounts (
    social_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    provider_email_verified BOOLEAN,
    scopes TEXT,
    linked_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT social_accounts_provider_chk CHECK (provider IN ('GOOGLE', 'KAKAO', 'NAVER', 'APPLE'))
);

-- Unique constraints for social accounts (allowing re-linking if revoked)
CREATE UNIQUE INDEX uk_social_provider_user_id ON social_accounts(provider, provider_user_id) WHERE revoked_at IS NULL AND is_active = true;
CREATE UNIQUE INDEX uk_user_provider ON social_accounts(user_id, provider) WHERE revoked_at IS NULL AND is_active = true;

CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);

-- 3. User Preferences Table
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    notification_enabled BOOLEAN NOT NULL DEFAULT true,
    dark_mode BOOLEAN NOT NULL DEFAULT false,
    risk_tolerance VARCHAR(32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT user_preferences_risk_tolerance_chk CHECK (risk_tolerance IS NULL OR risk_tolerance IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE'))
);

-- 4. Audit Logs Table
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

-- 5. Terms Table
CREATE TABLE terms (
    terms_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    terms_type VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT terms_type_chk CHECK (terms_type IN ('SERVICE', 'PRIVACY', 'MARKETING', 'LOCATION', 'THIRD_PARTY')),
    CONSTRAINT uk_terms_type UNIQUE (terms_type)
);

CREATE INDEX idx_terms_type ON terms(terms_type);
CREATE INDEX idx_terms_display_order ON terms(display_order);

-- 6. User Terms Agreements Table
CREATE TABLE user_terms_agreements (
    agreement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    terms_id BIGINT NOT NULL REFERENCES terms(terms_id) ON DELETE CASCADE,
    agreed BOOLEAN NOT NULL DEFAULT true,
    agreed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    CONSTRAINT uk_user_terms UNIQUE (user_id, terms_id)
);

CREATE INDEX idx_user_terms_agreements_user_id ON user_terms_agreements(user_id);
