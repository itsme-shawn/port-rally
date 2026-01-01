package api.repository.news;

import api.domain.news.NewsAssetRelation;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface NewsAssetRelationRepository extends ReactiveCrudRepository<NewsAssetRelation, UUID> {

    Flux<NewsAssetRelation> findAllByNewsId(UUID newsId);

    Flux<NewsAssetRelation> findAllByAssetId(UUID assetId);

    Mono<NewsAssetRelation> findByNewsIdAndAssetId(UUID newsId, UUID assetId);

    Mono<Boolean> existsByNewsIdAndAssetId(UUID newsId, UUID assetId);

    Mono<Void> deleteAllByNewsId(UUID newsId);
}
