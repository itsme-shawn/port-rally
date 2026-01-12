package api.repository.asset;

import api.domain.asset.AssetAiInsight;
import api.enums.asset.Recommendation;
import api.enums.portfolio.InsightStatus;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.util.UUID;

@Repository
public interface AssetAiInsightRepository extends ReactiveCrudRepository<AssetAiInsight, UUID> {

    Mono<AssetAiInsight> findByAssetIdAndInsightTypeAndAnalysisDate(
            Long assetId, String insightType, LocalDate analysisDate);

    Flux<AssetAiInsight> findAllByAssetIdOrderByAnalysisDateDesc(Long assetId);

    Flux<AssetAiInsight> findAllByAssetIdAndStatusOrderByAnalysisDateDesc(Long assetId, InsightStatus status);

    Flux<AssetAiInsight> findAllByRecommendationAndStatusOrderByAnalysisDateDesc(
            Recommendation recommendation, InsightStatus status);

    @Query("SELECT * FROM asset_ai_insights WHERE status = 'ACTIVE' ORDER BY analysis_date DESC LIMIT :limit")
    Flux<AssetAiInsight> findLatestActiveInsights(int limit);

    Mono<AssetAiInsight> findFirstByAssetIdAndStatusOrderByAnalysisDateDesc(Long assetId, InsightStatus status);
}
