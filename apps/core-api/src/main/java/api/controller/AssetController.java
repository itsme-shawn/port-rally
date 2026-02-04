package api.controller;

import api.dto.asset.AssetDetailResponse;
import api.dto.asset.AssetSearchResponse;
import api.service.asset.AssetService;
import api.service.asset.MarketDataServiceClient;
import api.dto.asset.AssetPriceResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/v1/assets")
@RequiredArgsConstructor
@Tag(name = "Asset", description = "자산 (종목) 정보 조회 API")
public class AssetController {

    private final AssetService assetService;
    private final MarketDataServiceClient marketDataServiceClient;

    /**
     * 자산 가격 조회 (Spot Price)
     * @param symbol 종목 코드
     * @param national 국가 코드 (KR, US 등)
     * @param market 거래소 코드 (KOSPI, NAS 등)
     * @return 현재가 정보
     */
    @GetMapping("/price")
    @Operation(summary = "자산 현재가 조회", description = "특정 종목의 현재가(Spot Price) 정보를 실시간으로 조회합니다.")
    public Mono<AssetPriceResponse> getAssetPrice(
        @RequestParam String symbol,
        @RequestParam(defaultValue = "KR") String national,
        @RequestParam(required = false) String market
    ) {
        log.info("GET /api/v1/assets/price - symbol: {}, national: {}, market: {}", symbol, national, market);
        return marketDataServiceClient.getSpotPrice(symbol, national, market);
    }

    /**
     * 자산 검색 (자동 완성 지원)
     * @param keyword 검색 키워드 (심볼, 종목명 등)
     * @param limit 반환할 최대 결과 수
     * @return 검색된 자산 목록
     */
    @GetMapping("/search")
    @Operation(summary = "자산 검색", description = "심볼, 종목명(한글/영어)으로 자산을 검색합니다. 자동 완성 기능을 지원합니다.")
    public Flux<AssetSearchResponse> searchAssets(
        @Parameter(description = "검색 키워드", required = true, example = "삼성")
        @RequestParam String keyword,
        @Parameter(description = "최대 결과 수", example = "10")
        @RequestParam(defaultValue = "10") int limit
    ) {
        log.info("GET /api/v1/assets/search - keyword: {}, limit: {}", keyword, limit);
        return assetService.searchAssets(keyword, limit);
    }

    /**
     * 자산 상세 조회 (ID 기준) - Deprecated
     * @param assetId 자산 ID
     * @return 자산 상세 정보
     * @deprecated assetId는 불안정한 식별자이므로 더 이상 사용하지 않습니다. /api/v1/assets/by-symbol/{identifier}를 사용하세요.
     */
    @GetMapping("/{assetId}")
    @Operation(summary = "자산 상세 조회 (ID 기준, Deprecated)", description = "특정 자산의 상세 정보를 조회합니다. `assetId`는 더 이상 사용되지 않으므로 `by-symbol/{identifier}` 엔드포인트를 사용해주세요.")
    @Deprecated
    public Mono<AssetDetailResponse> getAssetDetails(
        @Parameter(description = "자산 ID", required = true, example = "1")
        @PathVariable Long assetId
    ) {
        log.warn("Deprecated GET /api/v1/assets/{} - assetId: {}. Use /by-symbol/{identifier} instead.", assetId, assetId);
        return assetService.getAssetDetails(assetId);
    }

    /**
     * 자산 상세 조회 (심볼 식별자 기준)
     * @param identifier "{national}:{market}:{symbol}" 형식의 식별자
     * @param includePrice 현재가 정보 포함 여부
     * @return 자산 상세 정보
     */
    @GetMapping("/by-symbol/{identifier}")
    @Operation(summary = "자산 상세 조회 (심볼 식별자 기준)", description = "'national:market:symbol' 형식의 식별자로 자산의 상세 정보를 조회합니다. includePrice=true 옵션으로 현재가 정보를 함께 조회할 수 있습니다.")
    public Mono<AssetDetailResponse> getAssetDetailsBySymbol(
        @Parameter(description = "자산 식별자", required = true, example = "KR:KRX:005930")
        @PathVariable String identifier,
        @Parameter(description = "현재가 정보 포함 여부", example = "true")
        @RequestParam(defaultValue = "false") boolean includePrice
    ) {
        log.info("GET /api/v1/assets/by-symbol/{} - includePrice: {}", identifier, includePrice);
        return assetService.getAssetDetailsBySymbolIdentifier(identifier, includePrice);
    }
}
