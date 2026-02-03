package api.service.ocr.parser;

import java.util.List;

/**
 * 포트폴리오 텍스트 파서 인터페이스
 */
public interface PortfolioParser {

    /**
     * OCR 텍스트에서 종목 정보를 추출
     *
     * @param ocrText OCR로 추출한 텍스트
     * @return 파싱된 종목 정보 리스트
     */
    List<ParsedPosition> parse(String ocrText);

    /**
     * 파싱된 종목 정보
     */
    record ParsedPosition(
        String symbol,      // 티커 심볼
        String name,        // 종목명
        String quantity,    // 수량
        String averageCost, // 평균 매입가
        String currency     // 통화
    ) {}
}
