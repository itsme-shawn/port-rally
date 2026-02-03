package api.config;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

/**
 * OCR 관련 설정 (Tesseract)
 */
@Slf4j
@Getter
@Configuration
public class OcrConfig {

    @Value("${app.ocr.tesseract.data-path}")
    private String tesseractDataPath;

    @Value("${app.ocr.tesseract.language}")
    private String tesseractLanguage;
}
