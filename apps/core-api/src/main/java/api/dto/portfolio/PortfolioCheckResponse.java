package api.dto.portfolio;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "포트폴리오 존재 여부 응답")
public class PortfolioCheckResponse {

    @Schema(description = "포트폴리오 존재 여부", example = "true")
    private boolean hasPortfolio;

    public static PortfolioCheckResponse of(boolean hasPortfolio) {
        return PortfolioCheckResponse.builder()
            .hasPortfolio(hasPortfolio)
            .build();
    }
}
