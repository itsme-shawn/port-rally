package api.domain.user;

import api.enums.user.UserStatus;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 사용자 계정 정보
 */
@Table("users")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {

    @Id
    @Column("user_id")
    private UUID userId;  // null이면 INSERT (DB에서 gen_random_uuid() 생성)

    @Column("status")
    @Builder.Default
    private UserStatus status = UserStatus.PENDING;

    @Column("display_name")
    private String displayName;

    @Column("primary_email")
    private String primaryEmail;

    @Column("primary_email_verified")
    @Builder.Default
    private Boolean primaryEmailVerified = false;

    @Column("profile_image_url")
    private String profileImageUrl;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    @Column("last_login_at")
    private Instant lastLoginAt;

    @Column("signup_completed_at")
    private Instant signupCompletedAt;

    @Column("terms_accepted_at")
    private Instant termsAcceptedAt;

    @Column("deleted_at")
    private Instant deletedAt;

    // Business methods
    public boolean isDeleted() {
        return deletedAt != null;
    }

    public void softDelete() {
        this.deletedAt = Instant.now();
        this.status = UserStatus.DELETED;
    }

    public void verifyEmail() {
        if (isDeleted()) {
            throw new IllegalStateException("Cannot verify deleted user");
        }
        this.primaryEmailVerified = true;
    }

    public void activate() {
        this.status = UserStatus.ACTIVE;
        this.signupCompletedAt = Instant.now();
    }
}
