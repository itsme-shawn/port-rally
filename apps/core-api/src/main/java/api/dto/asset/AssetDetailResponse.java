package api.dto.asset;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;

import java.time.Instant;

@Builder
@Schema(description = "자산 상세 정보 응답")
public record AssetDetailResponse(
    @Schema(description = "자산 식별자 (national:market:symbol)", example = "KR:KRX:005930")
    String identifier,

    @Schema(description = "국가 (예: KR, US)", example = "KR")
    String national,

    @Schema(description = "시장 (예: KOSPI, NAS)", example = "KOSPI")
    String market,

    @Schema(description = "종목 심볼", example = "005930")
    String symbol,

    @Schema(description = "ISIN 코드", example = "KR7005930003")
    String isin,

    @Schema(description = "한글 종목명", example = "삼성전자")
    String nameKo,

    @Schema(description = "영어 종목명", example = "Samsung Electronics")
    String nameEn,

    @Schema(description = "자산 유형 (예: STOCK, ETF)", example = "STOCK")
    String assetType,

    @Schema(description = "통화 (예: KRW, USD)", example = "KRW")
    String currency,

    @Schema(description = "섹터 분류 체계", example = "GICS")
    String sectorScheme,

    @Schema(description = "섹터 태그 목록", example = "[\"Technology\", \"Semiconductor\"]")
    String[] sectorTags,

    @Schema(description = "생성 일시", example = "2024-01-01T00:00:00Z")
    Instant createdAt,

    @Schema(description = "수정 일시", example = "2024-01-01T00:00:00Z")
    Instant updatedAt,

    @Schema(description = "현재가 정보 (includePrice=true일 때만 포함)", nullable = true)
    AssetPriceResponse price
) {}
