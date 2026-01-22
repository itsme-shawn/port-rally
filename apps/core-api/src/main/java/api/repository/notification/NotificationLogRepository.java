package api.repository.notification;

import api.domain.notification.NotificationLog;
import api.enums.notification.DeliveryStatus;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface NotificationLogRepository extends ReactiveCrudRepository<NotificationLog, UUID> {

    Flux<NotificationLog> findAllByUserIdOrderByCreatedAtDesc(UUID userId);

    Flux<NotificationLog> findAllByUserIdAndIsReadFalseOrderByCreatedAtDesc(UUID userId);

    Flux<NotificationLog> findAllByUserIdAndNotificationTypeIdOrderByCreatedAtDesc(UUID userId, Long notificationTypeId);

    Flux<NotificationLog> findAllByDeliveryStatus(DeliveryStatus status);

    @Query("SELECT * FROM notifications_logs WHERE user_id = :userId ORDER BY created_at DESC LIMIT :limit")
    Flux<NotificationLog> findLatestByUserId(UUID userId, int limit);

    @Query("SELECT * FROM notifications_logs WHERE delivery_status = 'FAILED' AND retry_count < :maxRetries ORDER BY created_at")
    Flux<NotificationLog> findRetryableNotifications(int maxRetries);

    Mono<Long> countByUserIdAndIsReadFalse(UUID userId);

    Mono<Long> countByUserIdAndDeliveryStatus(UUID userId, DeliveryStatus status);
}
