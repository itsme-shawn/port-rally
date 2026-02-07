package api.domain.portfolio;

import api.enums.portfolio.InsightStatus;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

/**
 * 포트폴리오 종합 AI 분석 (개인별)
 */
@Table("portfolio_ai_insights")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PortfolioAiInsight {

    @Id
    @Column("portfolio_insight_id")
    private UUID portfolioInsightId;

    @Column("user_id")
    private UUID userId;

    @Column("portfolio_id")
    private UUID portfolioId;

    @Column("insight_type")
    private String insightType;

    @Column("analysis_date")
    private LocalDate analysisDate;

    @Column("title")
    private String title;

    @Column("executive_summary")
    private String executiveSummary;

    @Column("full_report")
    private String fullReport;

    @Column("health_score")
    private BigDecimal healthScore;

    @Column("risk_score")
    private BigDecimal riskScore;

    @Column("diversification_score")
    private BigDecimal diversificationScore;

    @Column("performance_score")
    private BigDecimal performanceScore;

    @Column("insights_data")
    private String insightsData;

    @Column("recommendations_data")
    private String recommendationsData;

    @Column("sectors_data")
    private String sectorsData;

    @Column("risk_metrics")
    private String riskMetrics;

    @Column("generated_by")
    private String generatedBy;

    @Column("version")
    @Builder.Default
    private Integer version = 1;

    @Column("status")
    @Builder.Default
    private InsightStatus status = InsightStatus.ACTIVE;

    @Column("is_read")
    @Builder.Default
    private Boolean isRead = false;

    @Column("read_at")
    private Instant readAt;

    @Column("generated_at")
    private Instant generatedAt;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    // Business methods
    public void markAsRead() {
        this.isRead = true;
        this.readAt = Instant.now();
    }

    public void supersede() {
        this.status = InsightStatus.SUPERSEDED;
    }
}
