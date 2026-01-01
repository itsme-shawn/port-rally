package api.repository.notification;

import api.domain.notification.NotificationType;
import api.enums.notification.NotificationCategory;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface NotificationTypeRepository extends ReactiveCrudRepository<NotificationType, UUID> {

    Mono<NotificationType> findByTypeName(String typeName);

    Flux<NotificationType> findAllByCategory(NotificationCategory category);

    Flux<NotificationType> findAllByIsActiveTrue();

    Flux<NotificationType> findAllByCategoryAndIsActiveTrue(NotificationCategory category);

    Flux<NotificationType> findAllByIsUserConfigurableTrue();

    Mono<Boolean> existsByTypeName(String typeName);
}
