package api.domain.portfolio;

import api.enums.portfolio.SourceType;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * 포트폴리오별 종목 보유 현황
 */
@Table("positions")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Position {

    @Id
    @Column("position_id")
    private UUID positionId;

    @Column("portfolio_id")
    private UUID portfolioId;

    @Column("asset_id")
    private Long assetId;

    @Column("quantity")
    private BigDecimal quantity;

    @Column("average_cost")
    private BigDecimal averageCost;

    @Column("cost_basis")
    private BigDecimal costBasis;

    @Column("source_type")
    private SourceType sourceType;

    @Column("value")
    private BigDecimal value;

    @Column("currency")
    @Builder.Default
    private String currency = "KRW";

    @Column("purchase_date")
    private java.time.LocalDate purchaseDate;

    @Column("broker")
    private String broker;

    @Column("account_alias")
    private String accountAlias;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    @Column("deleted_at")
    private Instant deletedAt;

    // Business methods
    public boolean isDeleted() {
        return deletedAt != null;
    }

    public void softDelete() {
        this.deletedAt = Instant.now();
    }

    public BigDecimal calculatePnl(BigDecimal currentPrice) {
        if (currentPrice == null || quantity == null || averageCost == null) {
            return BigDecimal.ZERO;
        }
        BigDecimal currentValue = currentPrice.multiply(quantity);
        return currentValue.subtract(costBasis != null ? costBasis : averageCost.multiply(quantity));
    }
}
