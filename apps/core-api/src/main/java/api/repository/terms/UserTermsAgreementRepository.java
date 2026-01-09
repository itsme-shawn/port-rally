package api.repository.terms;

import api.domain.terms.UserTermsAgreement;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface UserTermsAgreementRepository extends ReactiveCrudRepository<UserTermsAgreement, UUID> {

    Flux<UserTermsAgreement> findAllByUserId(UUID userId);

    Mono<UserTermsAgreement> findByUserIdAndTermsId(UUID userId, UUID termsId);

    Mono<Boolean> existsByUserIdAndTermsId(UUID userId, UUID termsId);

    @Query("SELECT COUNT(*) FROM user_terms_agreements WHERE user_id = :userId AND agreed = true")
    Mono<Long> countAgreedTermsByUserId(UUID userId);
}
