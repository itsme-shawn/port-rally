package api.repository.ocr;

import api.domain.ocr.UploadedImage;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.UUID;

@Repository
public interface UploadedImageRepository extends ReactiveCrudRepository<UploadedImage, UUID> {
    
    @Modifying
    @Query("UPDATE uploaded_images SET portfolio_id = :portfolioId WHERE image_id IN (:imageIds) AND user_id = :userId")
    Mono<Integer> updatePortfolioId(UUID portfolioId, List<UUID> imageIds, UUID userId);
}
