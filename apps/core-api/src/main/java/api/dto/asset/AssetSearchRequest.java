package api.dto.asset;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Size;
import lombok.Builder;

@Builder
@Schema(description = "자산 검색 요청")
public record AssetSearchRequest(
    @Size(min = 1, max = 100, message = "검색 키워드는 1자 이상 100자 이하입니다.")
    @Schema(description = "검색 키워드 (심볼, 종목명 등)", example = "삼성")
    String keyword
) {}
