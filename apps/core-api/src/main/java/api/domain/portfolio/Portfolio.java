package api.domain.portfolio;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 사용자의 포트폴리오
 */
@Table("portfolios")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Portfolio {

    @Id
    @Column("portfolio_id")
    private UUID portfolioId;

    @Column("user_id")
    private UUID userId;

    @Column("portfolio_name")
    private String portfolioName;

    @Column("is_primary")
    @Builder.Default
    private Boolean isPrimary = false;

    @Column("base_currency")
    @Builder.Default
    private String baseCurrency = "KRW";

    @Column("investment_type")
    private String investmentType;

    @Column("goal")
    private String goal;

    @Column("sector_focus")
    private String sectorFocus;

    @Column("tags")
    private String tags;  // JSONB stored as String

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

    public void restore() {
        this.deletedAt = null;
    }
}
