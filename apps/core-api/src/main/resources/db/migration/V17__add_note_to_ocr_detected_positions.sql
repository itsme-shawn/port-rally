ALTER TABLE ocr_detected_positions ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE ocr_detected_positions ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'KRW';

COMMENT ON COLUMN ocr_detected_positions.note IS '비고 (매칭 실패 사유 등)';
COMMENT ON COLUMN ocr_detected_positions.currency IS '통화 (KRW, USD 등)';
