-- =============================================
-- V9: Terms and User Terms Agreement Tables
-- =============================================

-- =============================================
-- 9.1 terms
-- =============================================
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
CREATE INDEX idx_terms_is_active ON terms(is_active);
CREATE INDEX idx_terms_display_order ON terms(display_order);

COMMENT ON TABLE terms IS '약관 정보';
COMMENT ON COLUMN terms.terms_type IS '약관 종류: SERVICE, PRIVACY, MARKETING, LOCATION, THIRD_PARTY';
COMMENT ON COLUMN terms.title IS '약관 제목';
COMMENT ON COLUMN terms.content IS '약관 전문';
COMMENT ON COLUMN terms.is_required IS '필수 약관 여부';
COMMENT ON COLUMN terms.is_active IS '활성 약관 여부';
COMMENT ON COLUMN terms.display_order IS '화면 표시 순서';

-- =============================================
-- 9.2 user_terms_agreements
-- =============================================
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
CREATE INDEX idx_user_terms_agreements_terms_id ON user_terms_agreements(terms_id);
CREATE INDEX idx_user_terms_agreements_agreed_at ON user_terms_agreements(agreed_at);

COMMENT ON TABLE user_terms_agreements IS '사용자 약관 동의 이력';
COMMENT ON COLUMN user_terms_agreements.agreed IS '동의 여부';
COMMENT ON COLUMN user_terms_agreements.agreed_at IS '동의 시각';
COMMENT ON COLUMN user_terms_agreements.ip_address IS '동의 시점의 IP 주소 (법적 근거)';
COMMENT ON COLUMN user_terms_agreements.user_agent IS '동의 시점의 User-Agent (법적 근거)';