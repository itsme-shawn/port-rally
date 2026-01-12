package api.dto.portfolio;

import api.domain.portfolio.Position;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

/**
 * 포지션 응답 DTO
 */
@Builder
public record PositionResponse(
    UUID positionId,
    UUID portfolioId,
    Long assetId,
    BigDecimal quantity,
    BigDecimal averageCost,
    BigDecimal costBasis,
    BigDecimal value,
    String currency,
    LocalDate purchaseDate,
    String broker,
    String accountAlias,
    String sourceType,
    Instant createdAt,
    Instant updatedAt
) {
    public static PositionResponse from(Position position) {
        return PositionResponse.builder()
            .positionId(position.getPositionId())
            .portfolioId(position.getPortfolioId())
            .assetId(position.getAssetId())
            .quantity(position.getQuantity())
            .averageCost(position.getAverageCost())
            .costBasis(position.getCostBasis())
            .value(position.getValue())
            .currency(position.getCurrency())
            .purchaseDate(position.getPurchaseDate())
            .broker(position.getBroker())
            .accountAlias(position.getAccountAlias())
            .sourceType(position.getSourceType() != null ? position.getSourceType().name() : null)
            .createdAt(position.getCreatedAt())
            .updatedAt(position.getUpdatedAt())
            .build();
    }
}
