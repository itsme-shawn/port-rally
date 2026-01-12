package api.repository.news;

import api.domain.news.NewsArticle;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.UUID;

@Repository
public interface NewsArticleRepository extends ReactiveCrudRepository<NewsArticle, Long> {

    Mono<NewsArticle> findBySourceUrl(String sourceUrl);

    Flux<NewsArticle> findAllBySource(String source);

    Mono<Boolean> existsBySourceUrl(String sourceUrl);

    @Query("SELECT * FROM news_articles ORDER BY published_at DESC LIMIT :limit")
    Flux<NewsArticle> findLatestNews(int limit);

    @Query("SELECT * FROM news_articles WHERE published_at >= :since ORDER BY published_at DESC")
    Flux<NewsArticle> findAllPublishedSince(Instant since);

    @Query("SELECT * FROM news_articles WHERE impact_score >= :minScore ORDER BY published_at DESC LIMIT :limit")
    Flux<NewsArticle> findHighImpactNews(double minScore, int limit);
}
