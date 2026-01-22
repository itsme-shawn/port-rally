package api.dto.portfolio;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.LocalDate;

@Builder
@Schema(description = "초기 포트폴리오에 추가될 종목 상세 정보")
public record InitialPositionRequest(
    @NotNull(message = "자산 ID는 필수입니다.")
    @Schema(description = "자산 ID", example = "1")
    Long assetId,

    @NotBlank(message = "종목 심볼은 필수입니다.")
    @Size(max = 50, message = "종목 심볼은 50자를 초과할 수 없습니다.")
    @Schema(description = "종목 심볼", example = "005930")
    String symbol,

    @NotBlank(message = "종목명은 필수입니다.")
    @Size(max = 255, message = "종목명은 255자를 초과할 수 없습니다.")
    @Schema(description = "종목명", example = "삼성전자")
    String name,

    @NotBlank(message = "시장은 필수입니다.")
    @Size(max = 50, message = "시장은 50자를 초과할 수 없습니다.")
    @Schema(description = "시장 (예: KRX, NAS)", example = "KRX")
    String market,

    @NotNull(message = "수량은 필수입니다.")
    @Schema(description = "보유 수량", example = "10")
    BigDecimal quantity,

    @NotNull(message = "평균 매입가는 필수입니다.")
    @Schema(description = "평균 매입가", example = "70000")
    BigDecimal averageCost,

    @NotNull(message = "포지션 가치는 필수입니다.")
    @Schema(description = "포지션 현재 가치", example = "720000")
    BigDecimal positionValue, // 신설 필드

    @NotBlank(message = "통화는 필수입니다.")
    @Size(max = 10, message = "통화는 10자를 초과할 수 없습니다.")
    @Schema(description = "통화 (예: KRW, USD)", example = "KRW")
    String currency,

    @Schema(description = "매수일 (선택)", example = "2024-01-01")
    LocalDate purchaseDate,

    @Size(max = 50, message = "증권사명은 50자를 초과할 수 없습니다.")
    @Schema(description = "증권사 (선택)", example = "토스증권")
    String broker,

    @Size(max = 100, message = "계좌 별명은 100자를 초과할 수 없습니다.")
    @Schema(description = "계좌 별명 (선택)", example = "월급통장")
    String accountAlias
) {}
