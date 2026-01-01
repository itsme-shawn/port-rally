package api.domain.notification;

import api.enums.notification.NotificationCategory;
import api.enums.notification.NotificationPriority;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 시스템에서 제공하는 알림 종류 정의 (마스터 데이터)
 */
@Table("notification_types")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationType {

    @Id
    @Column("notification_type_id")
    private UUID notificationTypeId;

    @Column("type_name")
    private String typeName;

    @Column("category")
    private NotificationCategory category;

    @Column("description")
    private String description;

    @Column("default_enabled")
    @Builder.Default
    private Boolean defaultEnabled = true;

    @Column("default_channels")
    @Builder.Default
    private String defaultChannels = "PUSH,IN_APP";

    @Column("is_user_configurable")
    @Builder.Default
    private Boolean isUserConfigurable = true;

    @Column("priority")
    @Builder.Default
    private NotificationPriority priority = NotificationPriority.NORMAL;

    @Column("icon")
    private String icon;

    @Column("is_active")
    @Builder.Default
    private Boolean isActive = true;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;
}
