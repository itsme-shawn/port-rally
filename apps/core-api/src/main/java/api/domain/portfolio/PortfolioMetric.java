package api.domain.portfolio;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

/**
 * 포트폴리오의 일별 성과 추적 및 지표
 */
@Table("portfolio_metrics")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PortfolioMetric {

    @Id
    @Column("portfolio_metrics_id")
    private UUID portfolioMetricsId;

    @Column("portfolio_id")
    private UUID portfolioId;

    @Column("snapshot_date")
    private LocalDate snapshotDate;

    @Column("total_value")
    private BigDecimal totalValue;

    @Column("total_cost")
    private BigDecimal totalCost;

    @Column("total_pnl")
    private BigDecimal totalPnl;

    @Column("total_pnl_percent")
    private BigDecimal totalPnlPercent;

    @Column("daily_pnl_percent")
    private BigDecimal dailyPnlPercent;

    @Column("weekly_pnl_percent")
    private BigDecimal weeklyPnlPercent;

    @Column("monthly_pnl_percent")
    private BigDecimal monthlyPnlPercent;

    @Column("ytd_pnl_percent")
    private BigDecimal ytdPnlPercent;

    @Column("volatility")
    private BigDecimal volatility;

    @Column("sharpe_ratio")
    private BigDecimal sharpeRatio;

    @Column("max_drawdown")
    private BigDecimal maxDrawdown;

    @Column("var_95")
    private BigDecimal var95;

    @Column("beta")
    private BigDecimal beta;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;
}
