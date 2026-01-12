-- =============================================
-- V11: Add missing fields to positions table
-- =============================================

ALTER TABLE positions
    ADD COLUMN currency VARCHAR(10) NOT NULL DEFAULT 'KRW',
    ADD COLUMN purchase_date DATE,
    ADD COLUMN broker VARCHAR(50),
    ADD COLUMN account_alias VARCHAR(100);

COMMENT ON COLUMN positions.currency IS '통화 (KRW, USD)';
COMMENT ON COLUMN positions.purchase_date IS '매수일 (옵션)';
COMMENT ON COLUMN positions.broker IS '증권사 (옵션)';
COMMENT ON COLUMN positions.account_alias IS '계좌 별명 (옵션)';
