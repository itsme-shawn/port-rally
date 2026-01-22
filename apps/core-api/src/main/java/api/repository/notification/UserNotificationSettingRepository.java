package api.repository.notification;

import api.domain.notification.UserNotificationSetting;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface UserNotificationSettingRepository extends ReactiveCrudRepository<UserNotificationSetting, UUID> {

    Flux<UserNotificationSetting> findAllByUserId(UUID userId);

    Flux<UserNotificationSetting> findAllByUserIdAndIsEnabledTrue(UUID userId);

    Mono<UserNotificationSetting> findByUserIdAndNotificationTypeId(UUID userId, Long notificationTypeId);

    Mono<Boolean> existsByUserIdAndNotificationTypeId(UUID userId, Long notificationTypeId);

    Mono<Void> deleteAllByUserId(UUID userId);
}
