package api.domain.asset;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * 종목별 기술적 지표
 */
@Table("assets_metrics")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AssetMetric {

    @Id
    @Column("indicator_id")
    private UUID indicatorId;

    @Column("asset_insight_id")
    private UUID assetInsightId;

    @Column("rsi_14")
    private BigDecimal rsi14;

    @Column("macd_value")
    private BigDecimal macdValue;

    @Column("macd_signal")
    private BigDecimal macdSignal;

    @Column("ma_20")
    private BigDecimal ma20;

    @Column("ma_50")
    private BigDecimal ma50;

    @Column("ma_200")
    private BigDecimal ma200;

    @Column("bollinger_upper")
    private BigDecimal bollingerUpper;

    @Column("bollinger_middle")
    private BigDecimal bollingerMiddle;

    @Column("bollinger_lower")
    private BigDecimal bollingerLower;

    @Column("volume_avg_20")
    private Long volumeAvg20;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;
}
