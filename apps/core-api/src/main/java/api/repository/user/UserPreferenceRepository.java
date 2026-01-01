package api.repository.user;

import api.domain.user.UserPreference;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface UserPreferenceRepository extends ReactiveCrudRepository<UserPreference, UUID> {

    Mono<UserPreference> findByUserId(UUID userId);
}
