package api.service.ocr;

import reactor.core.publisher.Mono;

import java.nio.file.Path;

/**
 * OCR 프로세서 인터페이스
 */
public interface OcrProcessor {

    /**
     * 이미지에서 텍스트를 추출하고 분석
     *
     * @param imagePath 이미지 파일 경로
     * @return OCR 결과 (추출된 텍스트와 신뢰도)
     */
    Mono<OcrProcessResult> process(Path imagePath);

    /**
     * OCR 처리 결과
     */
    record OcrProcessResult(
        String extractedText,
        double confidence,
        String processorName
    ) {}
}
