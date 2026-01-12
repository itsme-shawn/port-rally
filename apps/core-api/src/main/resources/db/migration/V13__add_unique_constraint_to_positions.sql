-- =============================================
-- V13: Add unique constraint to positions (portfolio_id, asset_id)
-- 한 포트폴리오 내에 동일한 종목은 하나만 존재해야 함
-- =============================================

-- 기존 중복 데이터가 있다면 정리가 필요할 수 있음 (현재는 개발 단계라 바로 적용)
CREATE UNIQUE INDEX uk_positions_portfolio_asset ON positions (portfolio_id, asset_id) WHERE deleted_at IS NULL;
