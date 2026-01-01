package api.repository.portfolio;

import api.domain.portfolio.PortfolioAiInsight;
import api.enums.portfolio.InsightStatus;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.util.UUID;

@Repository
public interface PortfolioAiInsightRepository extends ReactiveCrudRepository<PortfolioAiInsight, UUID> {

    Mono<PortfolioAiInsight> findByPortfolioIdAndInsightTypeAndAnalysisDate(
            UUID portfolioId, String insightType, LocalDate analysisDate);

    Flux<PortfolioAiInsight> findAllByPortfolioIdOrderByAnalysisDateDesc(UUID portfolioId);

    Flux<PortfolioAiInsight> findAllByUserIdOrderByCreatedAtDesc(UUID userId);

    Flux<PortfolioAiInsight> findAllByUserIdAndIsReadFalseOrderByCreatedAtDesc(UUID userId);

    @Query("SELECT * FROM portfolio_ai_insights WHERE user_id = :userId AND status = 'ACTIVE' ORDER BY analysis_date DESC LIMIT :limit")
    Flux<PortfolioAiInsight> findLatestActiveByUserId(UUID userId, int limit);

    Mono<PortfolioAiInsight> findFirstByPortfolioIdAndStatusOrderByAnalysisDateDesc(
            UUID portfolioId, InsightStatus status);

    Mono<Long> countByUserIdAndIsReadFalse(UUID userId);
}
