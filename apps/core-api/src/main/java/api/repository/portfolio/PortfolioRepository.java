package api.repository.portfolio;

import api.domain.portfolio.Portfolio;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface PortfolioRepository extends ReactiveCrudRepository<Portfolio, UUID> {

    Flux<Portfolio> findAllByUserId(UUID userId);

    Flux<Portfolio> findAllByUserIdAndDeletedAtIsNull(UUID userId);

    Mono<Portfolio> findByPortfolioIdAndDeletedAtIsNull(UUID portfolioId);

    Mono<Portfolio> findByUserIdAndIsPrimaryTrueAndDeletedAtIsNull(UUID userId);

    Mono<Long> countByUserIdAndDeletedAtIsNull(UUID userId);

    Mono<Boolean> existsByUserIdAndPortfolioNameAndDeletedAtIsNull(UUID userId, String portfolioName);

    @org.springframework.data.r2dbc.repository.Modifying
    @org.springframework.data.r2dbc.repository.Query("UPDATE portfolios SET is_primary = false WHERE user_id = :userId AND is_primary = true")
    Mono<Integer> resetPrimaryFlags(UUID userId);
}
