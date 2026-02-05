package api.service.ocr.parser;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 범용 포트폴리오 파서
 * 증권사에 구애받지 않는 공통 패턴을 인식
 */
@Slf4j
@Component
public class GenericPortfolioParser implements PortfolioParser {

    // 한글 종목명 패턴 (2-20자)
    private static final Pattern KOREAN_NAME_PATTERN = Pattern.compile("[가-힣]{2,20}");

    // 영문 종목명 패턴 (대문자 2-50자)
    private static final Pattern ENGLISH_NAME_PATTERN = Pattern.compile("[A-Z][a-zA-Z\\s\\.]{1,50}");

    // 티커 심볼 패턴 (6자리 숫자 또는 2-5자 대문자)
    private static final Pattern SYMBOL_PATTERN = Pattern.compile("\\b(\\d{6}|[A-Z]{2,5})\\b");

    // 종목명으로 인식하지 않을 블랙리스트 단어
    private static final List<String> NAME_BLACKLIST = List.of(
        "알수없는", "알수없는종목", "종목", "매수", "매도", "합계", "총합", "소계",
        "평가금액", "평가손익", "수익률", "보유수량", "평단가", "현재가",
        "증권사", "계좌", "포트폴리오", "자산", "종목명", "주식", "채권",
        "펀드", "예금", "적금", "보험", "부동산", "기타", "없음", "미정",
        "대기", "보류", "취소", "삭제", "수정", "변경", "추가", "등록"
    );

    // 수량 패턴 (콤마 포함 가능한 숫자, "주" 선택적)
    private static final Pattern QUANTITY_PATTERN = Pattern.compile("([\\d,]+(?:\\.\\d+)?)\\s*주?");

    // 가격 패턴 - 한국 원화
    private static final Pattern PRICE_KRW_PATTERN = Pattern.compile("([\\d,]+(?:\\.\\d+)?)[\\s]*원");

    // 가격 패턴 - 달러
    private static final Pattern PRICE_USD_PATTERN = Pattern.compile("\\$\\s*([\\d,]+(?:\\.\\d+)?)");

    // 가격 패턴 - 일반 숫자 (달러 심볼 없이)
    private static final Pattern PRICE_NUMBER_PATTERN = Pattern.compile("\\b([\\d,]+\\.\\d{2})\\b");

    // 통화 패턴
    private static final Pattern CURRENCY_PATTERN = Pattern.compile("\\b(KRW|USD|EUR|JPY|CNY)\\b");

    @Override
    public List<ParsedPosition> parse(String ocrText) {
        if (ocrText == null || ocrText.trim().isEmpty()) {
            log.warn("OCR 텍스트가 비어있습니다.");
            return List.of();
        }

        List<ParsedPosition> positions = new ArrayList<>();

        // 줄 단위로 파싱
        String[] lines = ocrText.split("\n");

        // 여러 줄을 합쳐서 파싱 (종목명과 수량/가격이 다른 줄에 있을 수 있음)
        for (int i = 0; i < lines.length; i++) {
            String currentLine = lines[i];
            String nextLine = i + 1 < lines.length ? lines[i + 1] : "";
            String combinedLine = currentLine + " " + nextLine;

            // 단일 줄 먼저 시도
            ParsedPosition position = parseLine(currentLine);
            if (position == null && !nextLine.isEmpty()) {
                // 실패하면 다음 줄과 합쳐서 시도
                position = parseLine(combinedLine);
            }

            if (position != null) {
                positions.add(position);
                log.debug("종목 파싱: {} ({}주, {})", position.name(), position.quantity(), position.averageCost());
            }
        }

        log.info("파싱 완료: {} 개 종목 추출", positions.size());
        return positions;
    }

    /**
     * 한 줄에서 종목 정보 추출
     */
    private ParsedPosition parseLine(String line) {
        if (line == null || line.trim().isEmpty()) {
            return null;
        }

        String symbol = extractSymbol(line);
        String name = extractName(line);
        String quantity = extractQuantity(line);
        String averageCost = extractPrice(line);
        String currency = detectCurrency(line, averageCost);

        // 최소한 이름 또는 심볼이 있어야 함
        if ((name == null || name.isEmpty()) && (symbol == null || symbol.isEmpty())) {
            return null;
        }

        // 수량 또는 가격 중 하나라도 있어야 함
        if ((quantity == null || quantity.isEmpty()) && (averageCost == null || averageCost.isEmpty())) {
            return null;
        }

        return new ParsedPosition(symbol, name, quantity, averageCost, currency);
    }

    private String extractSymbol(String line) {
        Matcher matcher = SYMBOL_PATTERN.matcher(line);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return null;
    }

    private String extractName(String line) {
        // 한글 우선 검색
        Matcher koreanMatcher = KOREAN_NAME_PATTERN.matcher(line);
        if (koreanMatcher.find()) {
            String name = koreanMatcher.group();
            // 블랙리스트 체크 (공백 제거 후 비교)
            String normalizedName = name.replace(" ", "");
            if (isBlacklistedName(normalizedName)) {
                log.debug("블랙리스트 단어 필터링: {}", name);
                return null;
            }
            return name;
        }

        // 영문 검색
        Matcher englishMatcher = ENGLISH_NAME_PATTERN.matcher(line);
        if (englishMatcher.find()) {
            String name = englishMatcher.group().trim();
            // 블랙리스트 체크 (소문자 변환 후 비교)
            if (isBlacklistedName(name.toLowerCase().replace(" ", ""))) {
                log.debug("블랙리스트 단어 필터링: {}", name);
                return null;
            }
            return name;
        }

        return null;
    }

    /**
     * 블랙리스트 단어 체크 (부분 매칭)
     */
    private boolean isBlacklistedName(String name) {
        String normalized = name.toLowerCase().replace(" ", "");
        return NAME_BLACKLIST.stream()
            .anyMatch(blacklisted -> normalized.contains(blacklisted.toLowerCase()));
    }

    private String extractQuantity(String line) {
        // 종목명 뒤의 첫 번째 소수점 숫자를 수량으로 간주
        Matcher matcher = Pattern.compile("\\b(\\d+\\.\\d+)\\s*주?").matcher(line);
        if (matcher.find()) {
            return matcher.group(1).replace(",", "");
        }

        // "주" 키워드가 있는 경우
        matcher = QUANTITY_PATTERN.matcher(line);
        if (matcher.find()) {
            return matcher.group(1).replace(",", "");
        }
        return null;
    }

    private String extractPrice(String line) {
        // 달러 가격 우선 ($1,404.37)
        Matcher matcher = PRICE_USD_PATTERN.matcher(line);
        if (matcher.find()) {
            return matcher.group(1).replace(",", "");
        }

        // 원화 가격 (70,000원)
        matcher = PRICE_KRW_PATTERN.matcher(line);
        if (matcher.find()) {
            return matcher.group(1).replace(",", "");
        }

        // 일반 숫자 (소수점 2자리, 1404.37)
        matcher = PRICE_NUMBER_PATTERN.matcher(line);
        if (matcher.find()) {
            return matcher.group(1).replace(",", "");
        }

        return null;
    }

    private String detectCurrency(String line, String price) {
        // 달러 심볼이 있으면 USD
        if (line.contains("$") || line.contains("USD")) {
            return "USD";
        }

        // 명시적 통화 표시
        Matcher matcher = CURRENCY_PATTERN.matcher(line);
        if (matcher.find()) {
            return matcher.group(1);
        }

        // 가격이 소수점 2자리면 USD로 추정
        if (price != null && price.matches("\\d+\\.\\d{2}")) {
            return "USD";
        }

        // 기본값 KRW
        return "KRW";
    }
}
