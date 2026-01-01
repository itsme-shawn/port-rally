package api.domain.asset;

import api.enums.asset.AssetType;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 투자 가능한 모든 자산의 마스터 정보
 */
@Table("assets_master")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Asset {

    @Id
    @Column("asset_id")
    private UUID assetId;

    @Column("symbol")
    private String symbol;

    @Column("market")
    private String market;

    @Column("asset_type")
    private AssetType assetType;

    @Column("name")
    private String name;

    @Column("sector")
    private String sector;

    @Column("industry")
    private String industry;

    @Column("country")
    private String country;

    @Column("currency")
    private String currency;

    @Column("is_active")
    @Builder.Default
    private Boolean isActive = true;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;
}
