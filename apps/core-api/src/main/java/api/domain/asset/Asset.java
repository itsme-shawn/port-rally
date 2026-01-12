package api.domain.asset;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;

/**
 * 투자 가능한 모든 자산의 마스터 정보 (securities_master 기반)
 */
@Table("assets_master")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Asset {

    @Id
    @Column("asset_id")
    private Long assetId;

    @Column("national")
    private String national;  // KR, US, HK, JP, CN, VN

    @Column("market")
    private String market;  // KOSPI, KOSDAQ, NAS, NYS, HKS, AMS

    @Column("symbol")
    private String symbol;

    @Column("isin")
    private String isin;

    @Column("name_ko")
    private String nameKo;

    @Column("name_en")
    private String nameEn;

    @Column("asset_type")
    private String assetType;  // STOCK/ETF/ETN/INDEX/WARRANT/CRYPTO/BOND/CASH/OTHER

    @Column("currency")
    private String currency;

    @Column("sector_scheme")
    private String sectorScheme;

    @Column("sector_tags")
    private String[] sectorTags;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;
}
