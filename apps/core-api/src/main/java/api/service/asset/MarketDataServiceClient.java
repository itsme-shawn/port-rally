package api.service.asset;

import api.dto.asset.AssetPriceResponse;
import api.redis.RedisKeys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class MarketDataServiceClient {

    private final WebClient webClient;
    private final ReactiveRedisTemplate<String, String> redisTemplate;

    public MarketDataServiceClient(
            WebClient.Builder webClientBuilder,
            @Value("${app.market-data.base-url}") String baseUrl,
            ReactiveRedisTemplate<String, String> redisTemplate) {
        this.webClient = webClientBuilder.baseUrl(baseUrl).build();
        this.redisTemplate = redisTemplate;
    }

    /**
     * 특정 종목의 실시간 현재가(Spot Price)를 조회합니다.
     * Redis 캐시를 먼저 확인하고, 없으면 market-data 서비스를 호출합니다.
     */
    public Mono<AssetPriceResponse> getSpotPrice(String symbol, String national, String market) {
        log.info("Requesting spot price for symbol: {}, national: {}, market: {}", symbol, national, market);

        // 1. Redis 캐시 확인
        String redisKey = RedisKeys.quote(national, market, symbol);

        return redisTemplate.opsForHash().entries(redisKey)
                .collectMap(Map.Entry::getKey, Map.Entry::getValue)
                .flatMap(cachedData -> {
                    if (cachedData.isEmpty()) {
                        log.info("Cache miss for {}, fetching from market-data API", redisKey);
                        return fetchFromMarketDataApi(symbol, national, market);
                    } else {
                        log.info("Cache hit for {}", redisKey);
                        return Mono.just(mapToAssetPriceResponse(cachedData));
                    }
                })
                .onErrorResume(e -> {
                    log.warn("Redis error, falling back to market-data API: {}", e.getMessage());
                    return fetchFromMarketDataApi(symbol, national, market);
                });
    }

    /**
     * market-data 서비스에 active_symbols 등록을 요청합니다.
     */
    public Mono<Void> registerActiveSymbols(String provider, List<String> symbols) {
        if (provider == null || provider.isBlank() || symbols == null || symbols.isEmpty()) {
            return Mono.empty();
        }

        return webClient.post()
                .uri(uriBuilder -> uriBuilder
                        .path("/v1/active-symbols/{provider}")
                        .build(provider))
                .bodyValue(Map.of("symbols", symbols))
                .retrieve()
                .bodyToMono(Void.class)
                .doOnSuccess(res -> log.info("Requested active_symbols registration: provider={}, symbols={}", provider, symbols))
                .doOnError(e -> log.warn("Failed to register active_symbols via market-data: {}", e.getMessage()))
                .onErrorResume(e -> Mono.empty());
    }

    /**
     * market-data API를 호출하여 현재가를 조회합니다.
     * (Redis 캐시 미스 또는 에러 시 호출됨)
     */
    private Mono<AssetPriceResponse> fetchFromMarketDataApi(String symbol, String national, String market) {
        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/v1/quotes/spot")
                        .queryParam("symbol", symbol)
                        .queryParam("national", national)
                        .queryParamIfPresent("market", java.util.Optional.ofNullable(market))
                        .build())
                .retrieve()
                .bodyToMono(AssetPriceResponse.class)
                .doOnSuccess(response -> log.info("Fetched spot price from market-data API for {}", symbol))
                .doOnError(e -> log.error("Error fetching spot price from market-data API: {}", e.getMessage()))
                .onErrorResume(e -> Mono.empty()); // 에러 시 빈 결과 반환
    }

    /**
     * Redis Hash 데이터를 AssetPriceResponse로 변환합니다.
     */
    private AssetPriceResponse mapToAssetPriceResponse(Map<Object, Object> cachedData) {
        return AssetPriceResponse.builder()
                .symbol(getStringValue(cachedData, "symbol"))
                .national(getStringValue(cachedData, "national"))
                .exchange(getStringValue(cachedData, "exchange"))
                .price(getBigDecimalValue(cachedData, "price"))
                .change(getBigDecimalValue(cachedData, "change"))
                .changeRate(getBigDecimalValue(cachedData, "change_rate"))
                .volume(getLongValue(cachedData, "volume"))
                .high(getBigDecimalValue(cachedData, "high"))
                .low(getBigDecimalValue(cachedData, "low"))
                .open(getBigDecimalValue(cachedData, "open"))
                .build();
    }

    private String getStringValue(Map<Object, Object> map, String key) {
        Object value = map.get(key);
        return value != null ? value.toString() : null;
    }

    private BigDecimal getBigDecimalValue(Map<Object, Object> map, String key) {
        Object value = map.get(key);
        if (value == null || value.toString().isEmpty()) {
            return null;
        }
        try {
            return new BigDecimal(value.toString());
        } catch (NumberFormatException e) {
            log.warn("Failed to parse BigDecimal for key {}: {}", key, value);
            return null;
        }
    }

    private Long getLongValue(Map<Object, Object> map, String key) {
        Object value = map.get(key);
        if (value == null || value.toString().isEmpty()) {
            return null;
        }
        try {
            return Long.parseLong(value.toString());
        } catch (NumberFormatException e) {
            log.warn("Failed to parse Long for key {}: {}", key, value);
            return null;
        }
    }
}
