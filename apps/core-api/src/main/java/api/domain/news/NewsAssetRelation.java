package api.domain.news;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * 뉴스와 종목의 연결 테이블 (N:N)
 */
@Table("news_asset_relations")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsAssetRelation {

    @Id
    @Column("news_asset_relation_id")
    private UUID newsAssetRelationId;

    @Column("news_id")
    private Long newsId;

    @Column("asset_id")
    private Long assetId;

    @Column("relevance_score")
    private BigDecimal relevanceScore;

    // Business methods
    public boolean isHighlyRelevant() {
        return relevanceScore != null &&
               relevanceScore.compareTo(new BigDecimal("0.7")) >= 0;
    }
}
