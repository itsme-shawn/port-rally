package api.repository.asset;

import api.domain.asset.Asset;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Repository
public interface AssetRepository extends ReactiveCrudRepository<Asset, Long> {

    // national + market + symbol 기준 조회
    Mono<Asset> findByNationalAndMarketAndSymbol(String national, String market, String symbol);

    Mono<Asset> findByMarketAndSymbol(String market, String symbol);

    Mono<Asset> findBySymbol(String symbol);

    Mono<Asset> findFirstByNameKo(String nameKo);

    Mono<Asset> findFirstByNameEn(String nameEn);

    Flux<Asset> findAllByMarket(String market);

    Flux<Asset> findAllByNational(String national);

    Flux<Asset> findAllByAssetType(String assetType);

    // ISIN으로 조회 (글로벌 종목 통합)
    Mono<Asset> findByIsin(String isin);

    // sector_tags 배열 검색 (PostgreSQL array contains)
    @Query("SELECT * FROM assets_master WHERE $1 = ANY(sector_tags)")
    Flux<Asset> findAllBySectorTag(String sectorTag);

    // sectorScheme 기준 조회
    Flux<Asset> findAllBySectorScheme(String sectorScheme);

    Mono<Boolean> existsByMarketAndSymbol(String market, String symbol);

    Mono<Boolean> existsByIsin(String isin);
}
