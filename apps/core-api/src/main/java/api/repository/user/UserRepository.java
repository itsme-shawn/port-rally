package api.repository.user;

import api.domain.user.User;
import api.enums.user.UserStatus;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface UserRepository extends ReactiveCrudRepository<User, UUID> {

    Mono<User> findByPrimaryEmail(String email);

    Mono<User> findByUserIdAndDeletedAtIsNull(UUID userId);

    Flux<User> findAllByDeletedAtIsNull();

    Mono<Boolean> existsByPrimaryEmail(String email);

    Mono<Boolean> existsByPrimaryEmailAndDeletedAtIsNull(String email);

    @Query("SELECT * FROM users WHERE status = :status AND deleted_at IS NULL")
    Flux<User> findByStatusAndDeletedAtIsNull(UserStatus status);

    Mono<Long> countByDeletedAtIsNull();
}
