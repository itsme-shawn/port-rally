package api.dto.portfolio;

import jakarta.validation.constraints.Size;
import lombok.Builder;

/**
 * 포트폴리오 수정 요청 DTO
 */
@Builder
public record UpdatePortfolioRequest(
    @Size(max = 100, message = "포트폴리오 이름은 100자를 초과할 수 없습니다.")
    String name,

    @Size(max = 500, message = "설명은 500자를 초과할 수 없습니다.")
    String description,

    @Size(max = 50, message = "투자 목적은 50자를 초과할 수 없습니다.")
    String goal,

    @Size(max = 50, message = "투자 유형은 50자를 초과할 수 없습니다.")
    String investmentType,

    Boolean isPrimary
) {}
