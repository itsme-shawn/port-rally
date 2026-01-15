package api.domain.ocr;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * OCR로 감지된 종목 정보 (사용자 확인 전)
 */
@Table("ocr_detected_positions")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OcrDetectedPosition {

    @Id
    @Column("ocr_detected_position_id")
    private UUID ocrDetectedPositionId;

    @Column("ocr_result_id")
    private UUID ocrResultId;

    @Column("detected_symbol")
    private String detectedSymbol;

    @Column("detected_name")
    private String detectedName;

    @Column("detected_market")
    private String detectedMarket;

    @Column("quantity")
    private BigDecimal quantity;

    @Column("average_cost")
    private BigDecimal averageCost;

    @Column("currency")
    @Builder.Default
    private String currency = "KRW";

    @Column("match_asset_id")
    private Long matchAssetId;

    @Column("is_confirmed")
    @Builder.Default
    private Boolean isConfirmed = false;

    @Column("confirmed_at")
    private Instant confirmedAt;

    @Column("note")
    private String note;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    // Business methods
    public void confirm() {
        this.isConfirmed = true;
        this.confirmedAt = Instant.now();
    }
}
