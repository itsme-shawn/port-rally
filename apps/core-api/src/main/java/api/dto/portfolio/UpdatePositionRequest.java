package api.dto.portfolio;

import jakarta.validation.constraints.DecimalMin;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 포지션 수정 요청 DTO
 */
@Builder
public record UpdatePositionRequest(
    Long assetId,

    @DecimalMin(value = "0.00000001", message = "수량은 0보다 커야 합니다.")
    BigDecimal quantity,

    @DecimalMin(value = "0.0", message = "평단가는 0 이상이어야 합니다.")
    BigDecimal averageCost,

    String currency,
    LocalDate purchaseDate,
    String broker,
    String accountAlias
) {}
