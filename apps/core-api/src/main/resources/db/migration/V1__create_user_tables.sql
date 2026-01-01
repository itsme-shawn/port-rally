-- =============================================
-- V1: User Management Tables
-- =============================================

-- Enum Types for User domain
CREATE TYPE user_status AS ENUM ('PENDING', 'ACTIVE', 'SUSPENDED', 'DELETED');
CREATE TYPE social_provider AS ENUM ('GOOGLE', 'KAKAO', 'NAVER', 'APPLE');
CREATE TYPE risk_tolerance AS ENUM ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE');

-- =============================================
-- 1.1 users
-- =============================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status user_status NOT NULL DEFAULT 'PENDING',
    display_name VARCHAR(100),
    primary_email VARCHAR(255),
    primary_email_verified BOOLEAN NOT NULL DEFAULT false,
    profile_image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    signup_completed_at TIMESTAMPTZ,
    terms_accepted_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- Unique constraint with partial index for non-null emails
CREATE UNIQUE INDEX uk_users_primary_email ON users(primary_email) WHERE primary_email IS NOT NULL;
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);

COMMENT ON TABLE users IS '사용자 계정 정보';
COMMENT ON COLUMN users.user_id IS 'PK - UUID';
COMMENT ON COLUMN users.status IS '계정 상태: PENDING, ACTIVE, SUSPENDED, DELETED';
COMMENT ON COLUMN users.display_name IS '닉네임';
COMMENT ON COLUMN users.primary_email IS '주 이메일';
COMMENT ON COLUMN users.primary_email_verified IS '이메일 인증 여부';
COMMENT ON COLUMN users.deleted_at IS '소프트 삭제 시각';

-- =============================================
-- 1.2 social_accounts
-- =============================================
CREATE TABLE social_accounts (
    social_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    provider social_provider NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    provider_email_verified BOOLEAN,
    scopes TEXT,
    linked_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT uk_social_provider_user_id UNIQUE (provider, provider_user_id),
    CONSTRAINT uk_user_provider UNIQUE (user_id, provider)
);

CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);

COMMENT ON TABLE social_accounts IS '소셜 로그인 연동 정보';
COMMENT ON COLUMN social_accounts.provider IS '소셜 제공자: GOOGLE, KAKAO, NAVER, APPLE';
COMMENT ON COLUMN social_accounts.provider_user_id IS '제공자의 사용자 ID';
COMMENT ON COLUMN social_accounts.scopes IS 'OAuth 스코프 (JSON or comma-separated)';

-- =============================================
-- 1.3 user_preferences
-- =============================================
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    notification_enabled BOOLEAN NOT NULL DEFAULT true,
    dark_mode BOOLEAN NOT NULL DEFAULT false,
    risk_tolerance risk_tolerance,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

COMMENT ON TABLE user_preferences IS '사용자 개인 설정 (1:1 관계)';
COMMENT ON COLUMN user_preferences.risk_tolerance IS '투자 성향: CONSERVATIVE, MODERATE, AGGRESSIVE';
