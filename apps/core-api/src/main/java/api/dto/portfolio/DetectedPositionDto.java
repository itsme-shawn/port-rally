package api.dto.portfolio;

import api.domain.ocr.OcrDetectedPosition;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * OCR로 감지된 종목 정보 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "OCR로 감지된 종목 정보")
public class DetectedPositionDto {

    @Schema(description = "감지된 포지션 임시 ID", example = "123e4567-e89b-12d3-a456-426614174000")
    private UUID detectedPositionId;

    @Schema(description = "종목코드", example = "005930")
    private String symbol;

    @Schema(description = "종목명", example = "삼성전자")
    private String name;

    @Schema(description = "시장", example = "KRX")
    private String market;

    @Schema(description = "보유 수량", example = "10")
    private BigDecimal quantity;

    @Schema(description = "평균 매입가", example = "70000")
    private BigDecimal averageCost;

    @Schema(description = "통화", example = "KRW")
    private String currency;

    @Schema(description = "매칭된 자산(DB) ID", example = "1")
    private Long assetId;

    @Schema(description = "비고 (매칭 실패 사유 등)", example = "종목 정보를 찾을 수 없습니다.")
    private String note;

    /**
     * OcrDetectedPosition 엔티티로부터 DTO 생성
     */
    public static DetectedPositionDto from(OcrDetectedPosition position) {
        return DetectedPositionDto.builder()
            .detectedPositionId(position.getOcrDetectedPositionId())
            .symbol(position.getDetectedSymbol())
            .name(position.getDetectedName())
            .market(position.getDetectedMarket())
            .quantity(position.getQuantity())
            .averageCost(position.getAverageCost())
            .currency(position.getCurrency())
            .assetId(position.getMatchAssetId())
            .note(position.getNote())
            .build();
    }
}
