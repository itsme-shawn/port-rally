package api.service.ocr;

import api.config.OcrConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.io.File;
import java.nio.file.Path;

/**
 * Tesseract 기반 무료 OCR 프로세서
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TesseractOcrProcessor implements OcrProcessor {

    private final OcrConfig ocrConfig;

    @Override
    public Mono<OcrProcessResult> process(Path imagePath) {
        return Mono.fromCallable(() -> {
            Tesseract tesseract = new Tesseract();
            tesseract.setDatapath(ocrConfig.getTesseractDataPath());
            tesseract.setLanguage(ocrConfig.getTesseractLanguage());

            try {
                String text = tesseract.doOCR(new File(imagePath.toString()));
                double confidence = calculateConfidence(text);

                log.info("Tesseract OCR 완료 - confidence: {}, text length: {}", confidence, text.length());
                return new OcrProcessResult(text, confidence, "Tesseract");
            } catch (TesseractException e) {
                log.error("Tesseract OCR 실패", e);
                throw new RuntimeException("Tesseract OCR failed", e);
            }
        }).subscribeOn(Schedulers.boundedElastic());
    }

    /**
     * 추출된 텍스트의 품질을 기반으로 신뢰도 계산
     * 간단한 휴리스틱: 텍스트 길이, 한글/영문 비율 등
     */
    private double calculateConfidence(String text) {
        if (text == null || text.trim().isEmpty()) {
            return 0.0;
        }

        // 텍스트 길이 기반 신뢰도 (최소 10자 이상)
        if (text.length() < 10) {
            return 0.3;
        }

        // 한글/영문/숫자 포함 여부 확인
        boolean hasKorean = text.matches(".*[ㄱ-ㅎㅏ-ㅣ가-힣]+.*");
        boolean hasEnglish = text.matches(".*[a-zA-Z]+.*");
        boolean hasDigits = text.matches(".*\\d+.*");

        double baseConfidence = 0.5;
        if (hasKorean) baseConfidence += 0.2;
        if (hasEnglish || hasDigits) baseConfidence += 0.2;

        // 줄바꿈이 있으면 구조화된 데이터일 가능성이 높음
        if (text.split("\n").length > 3) {
            baseConfidence += 0.1;
        }

        return Math.min(baseConfidence, 1.0);
    }
}
