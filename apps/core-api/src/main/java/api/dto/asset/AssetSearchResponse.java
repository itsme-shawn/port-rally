package api.dto.asset;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;

@Builder
@Schema(description = "자산 검색 응답")
public record AssetSearchResponse(
    @Schema(description = "자산 ID", example = "1")
    Long assetId,

    @Schema(description = "종목 심볼", example = "005930")
    String symbol,

    @Schema(description = "종목명 (한글 또는 영어)", example = "삼성전자")
    String name,

    @Schema(description = "시장 (예: KOSPI, NAS)", example = "KOSPI")
    String market,

    @Schema(description = "국가 (예: KR, US)", example = "KR")
    String national
) {}
