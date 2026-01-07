-- =============================================
-- V10: Allow re-registration after soft delete
-- =============================================

-- users: allow same email if the previous user is deleted
DROP INDEX IF EXISTS uk_users_primary_email;
CREATE UNIQUE INDEX uk_users_primary_email ON users(primary_email)
WHERE primary_email IS NOT NULL AND deleted_at IS NULL;

-- social_accounts: allow same provider user if the previous link is revoked
ALTER TABLE social_accounts DROP CONSTRAINT IF EXISTS uk_social_provider_user_id;
ALTER TABLE social_accounts DROP CONSTRAINT IF EXISTS uk_user_provider;
DROP INDEX IF EXISTS uk_social_provider_user_id;
DROP INDEX IF EXISTS uk_user_provider;

CREATE UNIQUE INDEX uk_social_provider_user_id
ON social_accounts(provider, provider_user_id)
WHERE revoked_at IS NULL AND is_active = true;

CREATE UNIQUE INDEX uk_user_provider
ON social_accounts(user_id, provider)
WHERE revoked_at IS NULL AND is_active = true;
