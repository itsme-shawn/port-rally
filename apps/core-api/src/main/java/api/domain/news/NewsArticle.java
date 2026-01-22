package api.domain.news;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * 뉴스 기사 저장
 */
@Table("news_articles")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsArticle {

    @Id
    @Column("news_id")
    private Long newsId;

    @Column("source")
    private String source;

    @Column("source_url")
    private String sourceUrl;

    @Column("title")
    private String title;

    @Column("content")
    private String content;

    @Column("summary")
    private String summary;

    @Column("published_at")
    private Instant publishedAt;

    @Column("sentiment_score")
    private BigDecimal sentimentScore;

    @Column("impact_score")
    private BigDecimal impactScore;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    // Business methods
    public boolean isPositive() {
        return sentimentScore != null &&
               sentimentScore.compareTo(BigDecimal.ZERO) > 0;
    }

    public boolean isNegative() {
        return sentimentScore != null &&
               sentimentScore.compareTo(BigDecimal.ZERO) < 0;
    }

    public boolean isHighImpact() {
        return impactScore != null &&
               impactScore.compareTo(new BigDecimal("0.7")) >= 0;
    }
}
