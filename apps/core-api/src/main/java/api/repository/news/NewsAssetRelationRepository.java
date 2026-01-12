package api.repository.news;

import api.domain.news.NewsAssetRelation;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface NewsAssetRelationRepository extends ReactiveCrudRepository<NewsAssetRelation, UUID> {

    Flux<NewsAssetRelation> findAllByNewsId(Long newsId);

    Flux<NewsAssetRelation> findAllByAssetId(Long assetId);

    Mono<NewsAssetRelation> findByNewsIdAndAssetId(Long newsId, Long assetId);

    Mono<Boolean> existsByNewsIdAndAssetId(Long newsId, Long assetId);

    Mono<Void> deleteAllByNewsId(Long newsId);
}
