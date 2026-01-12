package api.domain.notification;

import api.enums.notification.DeliveryChannel;
import api.enums.notification.DeliveryStatus;
import api.enums.notification.NotificationPriority;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 실제 발송된 알림의 기록 및 상태 관리
 */
@Table("notifications_logs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationLog {

    @Id
    @Column("notification_log_id")
    private UUID notificationLogId;

    @Column("user_id")
    private UUID userId;

    @Column("notification_type_id")
    private Long notificationTypeId;

    @Column("title")
    private String title;

    @Column("message")
    private String message;

    @Column("delivery_channel")
    private DeliveryChannel deliveryChannel;

    @Column("delivery_status")
    @Builder.Default
    private DeliveryStatus deliveryStatus = DeliveryStatus.PENDING;

    @Column("priority")
    @Builder.Default
    private NotificationPriority priority = NotificationPriority.NORMAL;

    @Column("source_type")
    private String sourceType;

    @Column("source_id")
    private UUID sourceId;

    @Column("related_portfolio_id")
    private UUID relatedPortfolioId;

    @Column("related_asset_id")
    private Long relatedAssetId;

    @Column("action_url")
    private String actionUrl;

    @Column("is_read")
    @Builder.Default
    private Boolean isRead = false;

    @Column("read_at")
    private Instant readAt;

    @Column("sent_at")
    private Instant sentAt;

    @Column("failed_reason")
    private String failedReason;

    @Column("retry_count")
    @Builder.Default
    private Integer retryCount = 0;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    // Business methods
    public void markAsRead() {
        this.isRead = true;
        this.readAt = Instant.now();
        this.deliveryStatus = DeliveryStatus.READ;
    }

    public void markAsSent() {
        this.deliveryStatus = DeliveryStatus.SENT;
        this.sentAt = Instant.now();
    }

    public void markAsFailed(String reason) {
        this.deliveryStatus = DeliveryStatus.FAILED;
        this.failedReason = reason;
        this.retryCount = (this.retryCount == null ? 0 : this.retryCount) + 1;
    }

    public boolean canRetry(int maxRetries) {
        return this.retryCount < maxRetries &&
               this.deliveryStatus == DeliveryStatus.FAILED;
    }
}
