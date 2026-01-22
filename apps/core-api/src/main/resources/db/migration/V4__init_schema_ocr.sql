-- =============================================
-- V4: OCR (Image Upload & Detection) Domain
-- =============================================

-- 1. Uploaded Images Table
CREATE TABLE uploaded_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    storage_url TEXT NOT NULL,
    upload_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    content_type VARCHAR(100),
    file_size BIGINT,
    hash_sha256 CHAR(64),
    retention_policy VARCHAR(50) NOT NULL DEFAULT '90_DAYS',
    retain_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uploaded_images_upload_status_chk CHECK (upload_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'))
);

CREATE INDEX idx_uploaded_images_user_id ON uploaded_images(user_id);
CREATE INDEX idx_uploaded_images_status ON uploaded_images(upload_status);

-- 2. OCR Results Table
CREATE TABLE ocr_results (
    ocr_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL UNIQUE REFERENCES uploaded_images(image_id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    raw_text TEXT,
    parsed_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT ocr_results_status_chk CHECK (status IN ('PENDING', 'VERIFIED', 'REJECTED', 'FAILED'))
);

-- 3. OCR Detected Positions Table
CREATE TABLE ocr_detected_positions (
    ocr_detected_position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ocr_result_id UUID NOT NULL REFERENCES ocr_results(ocr_result_id) ON DELETE CASCADE,
    detected_symbol VARCHAR(50),
    detected_name VARCHAR(255),
    detected_market VARCHAR(50),
    quantity NUMERIC(28,8),
    average_cost NUMERIC(28,8),
    match_asset_id BIGINT REFERENCES assets_master(asset_id) ON DELETE SET NULL,
    is_confirmed BOOLEAN NOT NULL DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- V12 & V17 Additions
    currency VARCHAR(10) DEFAULT 'KRW',
    note TEXT
);

CREATE INDEX idx_ocr_detected_positions_ocr_result ON ocr_detected_positions(ocr_result_id);
