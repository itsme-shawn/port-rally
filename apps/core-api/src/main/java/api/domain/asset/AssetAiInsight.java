package api.domain.asset;

import api.enums.asset.Recommendation;
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
 * 종목별 AI 분석 (전체 사용자 공용)
 */
@Table("asset_ai_insights")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AssetAiInsight {

    @Id
    @Column("asset_insight_id")
    private UUID assetInsightId;

    @Column("asset_id")
    private Long assetId;

    @Column("insight_type")
    private String insightType;

    @Column("analysis_date")
    private LocalDate analysisDate;

    @Column("title")
    private String title;

    @Column("summary")
    private String summary;

    @Column("content")
    private String content;

    @Column("sentiment_score")
    private BigDecimal sentimentScore;

    @Column("technical_score")
    private BigDecimal technicalScore;

    @Column("fundamental_score")
    private BigDecimal fundamentalScore;

    @Column("overall_score")
    private BigDecimal overallScore;

    @Column("recommendation")
    private Recommendation recommendation;

    @Column("confidence_level")
    private BigDecimal confidenceLevel;

    @Column("price_at_analysis")
    private BigDecimal priceAtAnalysis;

    @Column("target_price")
    private BigDecimal targetPrice;

    @Column("support_price")
    private BigDecimal supportPrice;

    @Column("resistance_price")
    private BigDecimal resistancePrice;

    @Column("key_factors")
    private String keyFactors;

    @Column("risk_factors")
    private String riskFactors;

    @Column("generated_by")
    private String generatedBy;

    @Column("version")
    @Builder.Default
    private Integer version = 1;

    @Column("status")
    @Builder.Default
    private InsightStatus status = InsightStatus.ACTIVE;

    @Column("view_count")
    @Builder.Default
    private Integer viewCount = 0;

    @Column("generated_at")
    private Instant generatedAt;

    @Column("expires_at")
    private Instant expiresAt;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    // Business methods
    public void incrementViewCount() {
        this.viewCount = (this.viewCount == null ? 0 : this.viewCount) + 1;
    }

    public void supersede() {
        this.status = InsightStatus.SUPERSEDED;
    }
}
