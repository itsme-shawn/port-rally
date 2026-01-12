package api.dto.portfolio;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

/**
 * 포지션 추가 요청 DTO
 */
@Builder
public record AddPositionRequest(
    @NotNull(message = "포트폴리오 ID는 필수입니다.")
    UUID portfolioId,

    @NotNull(message = "자산 ID는 필수입니다.")
    Long assetId,

    @NotNull(message = "수량은 필수입니다.")
    @DecimalMin(value = "0.00000001", message = "수량은 0보다 커야 합니다.")
    BigDecimal quantity,

    @NotNull(message = "평단가는 필수입니다.")
    @DecimalMin(value = "0.0", message = "평단가는 0 이상이어야 합니다.")
    BigDecimal averageCost,

    @NotBlank(message = "통화는 필수입니다.")
    String currency,

    LocalDate purchaseDate,

    String broker,

    String accountAlias
) {}
