-- =============================================
-- V6: Add match_confidence to OCR detected positions
-- =============================================

-- OCR 매칭 신뢰도 필드 추가
ALTER TABLE ocr_detected_positions
ADD COLUMN match_confidence DOUBLE PRECISION DEFAULT 0.0;

COMMENT ON COLUMN ocr_detected_positions.match_confidence IS 'Fuzzy matching으로 계산된 매칭 신뢰도 (0.0-1.0)';
