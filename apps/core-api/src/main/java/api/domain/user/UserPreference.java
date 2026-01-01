package api.domain.user;

import api.enums.user.RiskTolerance;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 사용자 개인 설정 (User와 1:1 관계)
 */
@Table("user_preferences")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserPreference {

    @Id
    @Column("user_id")
    private UUID userId;

    @Column("notification_enabled")
    @Builder.Default
    private Boolean notificationEnabled = true;

    @Column("dark_mode")
    @Builder.Default
    private Boolean darkMode = false;

    @Column("risk_tolerance")
    private RiskTolerance riskTolerance;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;
}
