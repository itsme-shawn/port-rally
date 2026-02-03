package api.service.asset;

import api.domain.asset.Asset;
import api.dto.asset.AssetDetailResponse;
import api.dto.asset.AssetSearchResponse;
import api.repository.asset.AssetRepository;
import api.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Slf4j
@Service
@RequiredArgsConstructor
public class AssetService {

    private final AssetRepository assetRepository;

    /**
     * 자산 검색 (심볼, 한글명, 영어명 포함)
     * 자동 완성 기능을 위해 부분 일치 검색을 지원합니다.
     *
     * @param keyword 검색 키워드
     * @param limit 검색 결과 최대 개수
     * @return AssetSearchResponse 목록
     */
    public Flux<AssetSearchResponse> searchAssets(String keyword, int limit) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return Flux.empty();
        }
        String searchKeyword = "%" + keyword.trim().toLowerCase() + "%";
        Pageable pageable = PageRequest.of(0, limit); // 첫 페이지, limit 개수

        return assetRepository.findByKeywordContaining(searchKeyword, pageable)
            .map(AssetService::mapToAssetSearchResponse);
    }

    /**
     * 자산 상세 조회 (ID 기준) - Deprecated
     * @deprecated assetId는 불안정한 식별자이므로 더 이상 사용하지 않습니다.
     *             getAssetDetailsBySymbolIdentifier를 사용하세요.
     */
    @Deprecated
    public Mono<AssetDetailResponse> getAssetDetails(Long assetId) {
        return assetRepository.findById(assetId)
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("자산을 찾을 수 없습니다.")))
            .map(AssetService::mapToAssetDetailResponse);
    }

    /**
     * 자산 상세 조회 (심볼 식별자 기준)
     *
     * @param identifier "{national}:{market}:{symbol}" 형식의 식별자
     * @return AssetDetailResponse
     */
    public Mono<AssetDetailResponse> getAssetDetailsBySymbolIdentifier(String identifier) {
        if (identifier == null || identifier.isBlank()) {
            return Mono.error(new IllegalArgumentException("심볼 식별자는 비어있을 수 없습니다."));
        }
        String[] parts = identifier.split(":");
        if (parts.length != 3) {
            return Mono.error(new IllegalArgumentException("심볼 식별자 형식이 올바르지 않습니다. (expected: national:market:symbol)"));
        }
        String national = parts[0];
        String market = parts[1];
        String symbol = parts[2];

        return assetRepository.findByNationalAndMarketAndSymbol(national, market, symbol)
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("자산을 찾을 수 없습니다: " + identifier)))
            .map(AssetService::mapToAssetDetailResponse);
    }

    private static AssetSearchResponse mapToAssetSearchResponse(Asset asset) {
        String name = asset.getNameKo() != null && !asset.getNameKo().isEmpty() ? asset.getNameKo() : asset.getNameEn();
        String identifier = String.format("%s:%s:%s", asset.getNational(), asset.getMarket(), asset.getSymbol());
        return AssetSearchResponse.builder()
            // .assetId(asset.getAssetId()) // assetId 더 이상 사용 안함
            .identifier(identifier)
            .symbol(asset.getSymbol())
            .name(name)
            .market(asset.getMarket())
            .national(asset.getNational())
            .build();
    }

    private static AssetDetailResponse mapToAssetDetailResponse(Asset asset) {
        String identifier = String.format("%s:%s:%s", asset.getNational(), asset.getMarket(), asset.getSymbol());
        return AssetDetailResponse.builder()
            // .assetId(asset.getAssetId()) // assetId 더 이상 사용 안함
            .identifier(identifier)
            .national(asset.getNational())
            .market(asset.getMarket())
            .symbol(asset.getSymbol())
            .isin(asset.getIsin())
            .nameKo(asset.getNameKo())
            .nameEn(asset.getNameEn())
            .assetType(asset.getAssetType())
            .currency(asset.getCurrency())
            .sectorScheme(asset.getSectorScheme())
            .sectorTags(asset.getSectorTags())
            .createdAt(asset.getCreatedAt())
            .updatedAt(asset.getUpdatedAt())
            .build();
    }
}
