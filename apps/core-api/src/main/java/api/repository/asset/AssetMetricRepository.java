package api.repository.asset;

import api.domain.asset.AssetMetric;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface AssetMetricRepository extends ReactiveCrudRepository<AssetMetric, UUID> {

    Flux<AssetMetric> findAllByAssetInsightId(UUID assetInsightId);

    Mono<AssetMetric> findFirstByAssetInsightIdOrderByCreatedAtDesc(UUID assetInsightId);
}
