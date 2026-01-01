package api.repository.ocr;

import api.domain.ocr.UploadedImage;
import api.enums.ocr.UploadStatus;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface UploadedImageRepository extends ReactiveCrudRepository<UploadedImage, UUID> {

    Flux<UploadedImage> findAllByUserId(UUID userId);

    Flux<UploadedImage> findAllByPortfolioId(UUID portfolioId);

    Flux<UploadedImage> findAllByUploadStatus(UploadStatus status);

    Mono<UploadedImage> findByHashSha256(String hashSha256);

    Mono<Boolean> existsByHashSha256(String hashSha256);

    Mono<Long> countByUserIdAndUploadStatus(UUID userId, UploadStatus status);
}
