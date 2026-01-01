package api.repository.user;

import api.domain.user.SocialAccount;
import api.enums.user.SocialProvider;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface SocialAccountRepository extends ReactiveCrudRepository<SocialAccount, UUID> {

    Mono<SocialAccount> findByProviderAndProviderUserId(SocialProvider provider, String providerUserId);

    Mono<SocialAccount> findByUserIdAndProvider(UUID userId, SocialProvider provider);

    Flux<SocialAccount> findAllByUserId(UUID userId);

    Flux<SocialAccount> findAllByUserIdAndIsActiveTrue(UUID userId);

    Mono<Boolean> existsByProviderAndProviderUserId(SocialProvider provider, String providerUserId);
}
