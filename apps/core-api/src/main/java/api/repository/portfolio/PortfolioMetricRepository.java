package api.repository.portfolio;

import api.domain.portfolio.PortfolioMetric;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.util.UUID;

@Repository
public interface PortfolioMetricRepository extends ReactiveCrudRepository<PortfolioMetric, UUID> {

    Mono<PortfolioMetric> findByPortfolioIdAndSnapshotDate(UUID portfolioId, LocalDate snapshotDate);

    Flux<PortfolioMetric> findAllByPortfolioIdOrderBySnapshotDateDesc(UUID portfolioId);

    @Query("SELECT * FROM portfolio_metrics WHERE portfolio_id = :portfolioId ORDER BY snapshot_date DESC LIMIT :limit")
    Flux<PortfolioMetric> findLatestByPortfolioId(UUID portfolioId, int limit);

    Mono<PortfolioMetric> findFirstByPortfolioIdOrderBySnapshotDateDesc(UUID portfolioId);

    @Query("SELECT * FROM portfolio_metrics WHERE portfolio_id = :portfolioId AND snapshot_date >= :startDate AND snapshot_date <= :endDate ORDER BY snapshot_date")
    Flux<PortfolioMetric> findByPortfolioIdAndDateRange(UUID portfolioId, LocalDate startDate, LocalDate endDate);
}
