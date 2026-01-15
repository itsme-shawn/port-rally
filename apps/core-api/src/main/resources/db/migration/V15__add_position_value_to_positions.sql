-- =============================================
-- V15: positions 테이블에 position_value 컬럼 추가
-- =============================================

ALTER TABLE positions
    ADD COLUMN position_value NUMERIC(28,8);
