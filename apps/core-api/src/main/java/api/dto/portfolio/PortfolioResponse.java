package api.dto.portfolio;

import api.domain.portfolio.Portfolio;
import lombok.Builder;

import java.time.Instant;
import java.util.UUID;

/**
 * 포트폴리오 응답 DTO
 */
@Builder
public record PortfolioResponse(
    UUID portfolioId,
    UUID userId,
    String name,
    String description,
    boolean isPrimary,
    String baseCurrency,
    String goal,
    String investmentType,
    Instant createdAt,
    Instant updatedAt
) {
    public static PortfolioResponse from(Portfolio portfolio) {
        return PortfolioResponse.builder()
            .portfolioId(portfolio.getPortfolioId())
            .userId(portfolio.getUserId())
            .name(portfolio.getPortfolioName())
            .description(portfolio.getDescription())
            .isPrimary(portfolio.getIsPrimary())
            .baseCurrency(portfolio.getBaseCurrency())
            .goal(portfolio.getGoal())
            .investmentType(portfolio.getInvestmentType())
            .createdAt(portfolio.getCreatedAt())
            .updatedAt(portfolio.getUpdatedAt())
            .build();
    }
}
