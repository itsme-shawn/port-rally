-- =============================================
-- V9: Terms and User Terms Agreement Tables
-- =============================================

-- =============================================
-- 9.1 terms
-- =============================================
CREATE TABLE terms (
    terms_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    terms_type VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT terms_type_chk CHECK (terms_type IN ('SERVICE', 'PRIVACY', 'MARKETING', 'LOCATION', 'THIRD_PARTY'))
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
    terms_id UUID NOT NULL REFERENCES terms(terms_id) ON DELETE CASCADE,
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

-- =============================================
-- 9.3 Insert Default Terms
-- =============================================
INSERT INTO terms (terms_type, title, content, is_required, is_active, display_order)
VALUES
    ('SERVICE', '서비스 이용약관', '
포트폴리오 랠리 서비스 이용약관

제1조 (목적)
본 약관은 포트폴리오 랠리(이하 "회사"라 합니다)가 제공하는 포트폴리오 관리 서비스(이하 "서비스"라 합니다)의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.

제2조 (정의)
1. "서비스"란 회사가 제공하는 포트폴리오 추적, 분석, AI 인사이트 등의 모든 서비스를 의미합니다.
2. "이용자"란 본 약관에 따라 회사가 제공하는 서비스를 이용하는 자를 말합니다.

제3조 (약관의 효력 및 변경)
1. 본 약관은 서비스를 이용하고자 하는 모든 이용자에게 그 효력이 발생합니다.
2. 회사는 필요한 경우 관련 법령을 위배하지 않는 범위에서 본 약관을 변경할 수 있습니다.
    ', true, true, 1),

    ('PRIVACY', '개인정보 처리방침', '
포트폴리오 랠리 개인정보 처리방침

포트폴리오 랠리(이하 "회사"라 합니다)는 이용자의 개인정보를 중요시하며, 개인정보 보호법을 준수하고 있습니다.

제1조 (개인정보의 처리 목적)
회사는 다음의 목적을 위하여 개인정보를 처리합니다. 처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 이용 목적이 변경되는 경우에는 개인정보 보호법에 따라 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.

1. 회원 가입 및 관리
- 회원 가입 의사 확인, 회원제 서비스 제공에 따른 본인 식별·인증
- 회원자격 유지·관리, 서비스 부정이용 방지

2. 서비스 제공
- 포트폴리오 데이터 저장 및 분석
- AI 기반 인사이트 제공

제2조 (개인정보의 처리 및 보유 기간)
회사는 법령에 따른 개인정보 보유·이용기간 또는 이용자로부터 개인정보를 수집 시에 동의받은 개인정보 보유·이용기간 내에서 개인정보를 처리·보유합니다.

제3조 (정보주체의 권리·의무 및 그 행사방법)
이용자는 개인정보주체로서 다음과 같은 권리를 행사할 수 있습니다.
1. 개인정보 열람요구
2. 오류 등이 있을 경우 정정 요구
3. 삭제요구
4. 처리정지 요구
    ', true, true, 2),

    ('MARKETING', '마케팅 정보 수신 동의', '
마케팅 정보 수신 동의

포트폴리오 랠리(이하 "회사"라 합니다)는 다음과 같이 마케팅 정보를 제공합니다.

1. 제공 목적
- 이벤트, 프로모션, 신규 서비스 등의 광고성 정보 제공
- 맞춤형 서비스 및 상품 추천

2. 수신 방법
- 이메일, 푸시 알림, SMS 등

3. 동의 철회
- 언제든지 마케팅 정보 수신 동의를 철회할 수 있습니다.
- 설정 > 알림 설정에서 수신 동의를 변경할 수 있습니다.

4. 동의하지 않을 권리
- 마케팅 정보 수신에 동의하지 않을 수 있으며, 동의하지 않아도 서비스 이용에는 제한이 없습니다.
    ', false, true, 3),

    ('LOCATION', '위치정보 이용약관', '
위치정보 이용약관

포트폴리오 랠리(이하 "회사"라 합니다)는 이용자의 위치정보를 다음과 같이 이용합니다.

제1조 (위치정보의 수집 목적)
1. 지역별 맞춤 투자 정보 제공
2. 지역 기반 이벤트 및 프로모션 안내

제2조 (위치정보의 보유 기간)
회사는 위치정보를 수집한 시점으로부터 1년간 보유합니다.

제3조 (위치정보 이용 동의 철회)
이용자는 언제든지 위치정보 이용 동의를 철회할 수 있습니다.

제4조 (동의하지 않을 권리)
위치정보 이용에 동의하지 않을 수 있으며, 동의하지 않아도 기본 서비스 이용에는 제한이 없습니다.
    ', false, true, 4);
