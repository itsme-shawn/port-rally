package api.domain.user;

import api.enums.user.SocialProvider;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 소셜 로그인 연동 정보
 */
@Table("social_accounts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SocialAccount {

    @Id
    @Column("social_account_id")
    private UUID socialAccountId;

    @Column("user_id")
    private UUID userId;

    @Column("provider")
    private SocialProvider provider;

    @Column("provider_user_id")
    private String providerUserId;

    @Column("provider_email")
    private String providerEmail;

    @Column("provider_email_verified")
    private Boolean providerEmailVerified;

    @Column("scopes")
    private String scopes;

    @Column("linked_at")
    private Instant linkedAt;

    @Column("last_login_at")
    private Instant lastLoginAt;

    @Column("is_active")
    @Builder.Default
    private Boolean isActive = true;

    @Column("revoked_at")
    private Instant revokedAt;

    // Business methods
    public void revoke() {
        this.isActive = false;
        this.revokedAt = Instant.now();
    }

    public void updateLastLogin() {
        this.lastLoginAt = Instant.now();
    }
}
