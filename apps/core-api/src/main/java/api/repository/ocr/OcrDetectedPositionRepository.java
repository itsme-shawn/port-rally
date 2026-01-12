package api.repository.ocr;

import api.domain.ocr.OcrDetectedPosition;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface OcrDetectedPositionRepository extends ReactiveCrudRepository<OcrDetectedPosition, UUID> {

    Flux<OcrDetectedPosition> findAllByOcrResultId(UUID ocrResultId);

    Flux<OcrDetectedPosition> findAllByOcrResultIdAndIsConfirmedFalse(UUID ocrResultId);

    Flux<OcrDetectedPosition> findAllByOcrResultIdAndIsConfirmedTrue(UUID ocrResultId);

    Flux<OcrDetectedPosition> findAllByMatchAssetId(Long matchAssetId);

    Mono<Long> countByOcrResultIdAndIsConfirmedFalse(UUID ocrResultId);
}
