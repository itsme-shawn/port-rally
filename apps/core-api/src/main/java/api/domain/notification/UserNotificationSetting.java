package api.domain.notification;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.time.LocalTime;
import java.util.UUID;

/**
 * 사용자별 알림 수신 설정
 */
@Table("user_notification_settings")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserNotificationSetting {

    @Id
    @Column("settings_id")
    private UUID settingsId;

    @Column("user_id")
    private UUID userId;

    @Column("notification_type_id")
    private UUID notificationTypeId;

    @Column("is_enabled")
    @Builder.Default
    private Boolean isEnabled = true;

    @Column("delivery_channels")
    @Builder.Default
    private String deliveryChannels = "PUSH,IN_APP";

    @Column("quiet_hours_start")
    private LocalTime quietHoursStart;

    @Column("quiet_hours_end")
    private LocalTime quietHoursEnd;

    @Column("preferred_time")
    private LocalTime preferredTime;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    // Business methods
    public boolean isInQuietHours(LocalTime currentTime) {
        if (quietHoursStart == null || quietHoursEnd == null) {
            return false;
        }
        if (quietHoursStart.isBefore(quietHoursEnd)) {
            return !currentTime.isBefore(quietHoursStart) && currentTime.isBefore(quietHoursEnd);
        } else {
            // Quiet hours span midnight
            return !currentTime.isBefore(quietHoursStart) || currentTime.isBefore(quietHoursEnd);
        }
    }
}
