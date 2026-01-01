package api.repository.ocr;

import api.domain.ocr.OcrResult;
import api.enums.ocr.OcrStatus;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface OcrResultRepository extends ReactiveCrudRepository<OcrResult, UUID> {

    Mono<OcrResult> findByImageId(UUID imageId);

    Flux<OcrResult> findAllByStatus(OcrStatus status);

    Mono<Boolean> existsByImageId(UUID imageId);
}
