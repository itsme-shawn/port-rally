package api.repository.terms;

import api.domain.terms.Terms;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface TermsRepository extends ReactiveCrudRepository<Terms, UUID> {

    Flux<Terms> findAllByIsActiveTrueOrderByDisplayOrderAsc();

    Flux<Terms> findAllByIsActiveTrueAndIsRequiredTrue();

    Mono<Terms> findByTermsTypeAndIsActiveTrue(String termsType);

    Mono<Long> countByIsActiveTrueAndIsRequiredTrue();
}
