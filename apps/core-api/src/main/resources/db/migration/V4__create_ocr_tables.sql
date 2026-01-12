-- =============================================
-- V4: OCR (Image Upload) Tables
-- =============================================

-- Enum Types for OCR domain
CREATE TYPE upload_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
CREATE TYPE ocr_status AS ENUM ('PENDING', 'VERIFIED', 'REJECTED', 'FAILED');

-- =============================================
-- 5.1 uploaded_images
-- =============================================
CREATE TABLE uploaded_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    storage_url TEXT NOT NULL,
    upload_status upload_status NOT NULL DEFAULT 'PENDING',
    content_type VARCHAR(100),
    file_size BIGINT,
    hash_sha256 CHAR(64),
    retention_policy VARCHAR(50) NOT NULL DEFAULT '90_DAYS',
    retain_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uploaded_images_user_id ON uploaded_images(user_id);
CREATE INDEX idx_uploaded_images_portfolio_id ON uploaded_images(portfolio_id);
CREATE INDEX idx_uploaded_images_status ON uploaded_images(upload_status);
CREATE INDEX idx_uploaded_images_hash ON uploaded_images(hash_sha256);

COMMENT ON TABLE uploaded_images IS '사용자가 업로드한 계좌 이미지';
COMMENT ON COLUMN uploaded_images.storage_url IS 'S3 URL';
COMMENT ON COLUMN uploaded_images.hash_sha256 IS '파일 해시 (중복 방지)';
COMMENT ON COLUMN uploaded_images.retention_policy IS '보관 정책';

-- =============================================
-- 5.2 ocr_results
-- =============================================
CREATE TABLE ocr_results (
    ocr_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL UNIQUE REFERENCES uploaded_images(image_id) ON DELETE CASCADE,
    status ocr_status NOT NULL DEFAULT 'PENDING',
    raw_text TEXT,
    parsed_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_ocr_results_status ON ocr_results(status);

COMMENT ON TABLE ocr_results IS 'AI가 이미지에서 추출한 OCR 결과';
COMMENT ON COLUMN ocr_results.raw_text IS 'OCR 원문';
COMMENT ON COLUMN ocr_results.parsed_data IS '구조화된 데이터 (JSON)';

-- =============================================
-- 5.3 ocr_detected_positions
-- =============================================
CREATE TABLE ocr_detected_positions (
    ocr_detected_position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ocr_result_id UUID NOT NULL REFERENCES ocr_results(ocr_result_id) ON DELETE CASCADE,
    detected_symbol VARCHAR(50),
    detected_name VARCHAR(255),
    detected_market VARCHAR(50),
    quantity NUMERIC(28,8),
    average_cost NUMERIC(28,8),
    match_asset_id BIGINT REFERENCES assets_master(asset_id) ON DELETE SET NULL,
    match_confidence NUMERIC(5,4),
    is_confirmed BOOLEAN NOT NULL DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ocr_detected_positions_ocr_result ON ocr_detected_positions(ocr_result_id);
CREATE INDEX idx_ocr_detected_positions_match_asset ON ocr_detected_positions(match_asset_id);
CREATE INDEX idx_ocr_detected_positions_confirmed ON ocr_detected_positions(is_confirmed);

COMMENT ON TABLE ocr_detected_positions IS 'OCR로 감지된 종목 정보 (사용자 확인 전)';
COMMENT ON COLUMN ocr_detected_positions.detected_symbol IS 'OCR 인식 심볼';
COMMENT ON COLUMN ocr_detected_positions.match_asset_id IS '매칭된 자산 FK';
COMMENT ON COLUMN ocr_detected_positions.match_confidence IS '매칭 신뢰도 (0~1)';
COMMENT ON COLUMN ocr_detected_positions.is_confirmed IS '사용자 확인 여부';
