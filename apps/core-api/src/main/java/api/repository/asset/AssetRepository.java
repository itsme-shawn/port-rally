package api.repository.asset;

import api.domain.asset.Asset;
import api.enums.asset.AssetType;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface AssetRepository extends ReactiveCrudRepository<Asset, UUID> {

    Mono<Asset> findByMarketAndSymbolAndAssetType(String market, String symbol, AssetType assetType);

    Mono<Asset> findByMarketAndSymbol(String market, String symbol);

    Flux<Asset> findAllByMarket(String market);

    Flux<Asset> findAllByAssetType(AssetType assetType);

    Flux<Asset> findAllByIsActiveTrue();

    Flux<Asset> findAllBySector(String sector);

    Mono<Boolean> existsByMarketAndSymbol(String market, String symbol);
}
