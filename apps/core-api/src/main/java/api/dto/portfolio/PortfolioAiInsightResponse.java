package api.dto.portfolio;

import api.domain.portfolio.PortfolioAiInsight;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonRawValue;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Builder
public record PortfolioAiInsightResponse(
        UUID portfolioInsightId,
        UUID portfolioId,
        String insightType,
        LocalDate analysisDate,
        String title,
        String executiveSummary,
        String fullReport,
        BigDecimal healthScore,
        BigDecimal riskScore,
        BigDecimal diversificationScore,
        BigDecimal performanceScore,

        @JsonRawValue String insightsData,

        @JsonRawValue String recommendationsData,

        @JsonRawValue String sectorsData,

        @JsonRawValue String riskMetrics,

        String generatedBy,

        @JsonFormat(shape = JsonFormat.Shape.STRING) Instant generatedAt) {
    public static PortfolioAiInsightResponse from(PortfolioAiInsight insight) {
        if (insight == null)
            return null;

        return PortfolioAiInsightResponse.builder()
                .portfolioInsightId(insight.getPortfolioInsightId())
                .portfolioId(insight.getPortfolioId())
                .insightType(insight.getInsightType())
                .analysisDate(insight.getAnalysisDate())
                .title(insight.getTitle())
                .executiveSummary(insight.getExecutiveSummary())
                .fullReport(insight.getFullReport())
                .healthScore(insight.getHealthScore())
                .riskScore(insight.getRiskScore())
                .diversificationScore(insight.getDiversificationScore())
                .performanceScore(insight.getPerformanceScore())
                .insightsData(insight.getInsightsData())
                .recommendationsData(insight.getRecommendationsData())
                .sectorsData(insight.getSectorsData())
                .riskMetrics(insight.getRiskMetrics())
                .generatedBy(insight.getGeneratedBy())
                .generatedAt(insight.getGeneratedAt())
                .build();
    }
}
