package api.service.asset;

import api.dto.asset.AssetPriceResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Slf4j
@Service
public class MarketDataServiceClient {

    private final WebClient webClient;

    public MarketDataServiceClient(WebClient.Builder webClientBuilder, 
                                 @Value("${app.market-data.base-url}") String baseUrl) {
        this.webClient = webClientBuilder.baseUrl(baseUrl).build();
    }

    /**
     * 특정 종목의 실시간 현재가(Spot Price)를 market-data 서비스에서 조회합니다.
     */
    public Mono<AssetPriceResponse> getSpotPrice(String symbol, String national, String market) {
        log.info("Requesting spot price for symbol: {}, national: {}, market: {}", symbol, national, market);
        
        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/v1/quotes/spot")
                        .queryParam("symbol", symbol)
                        .queryParam("national", national)
                        .queryParamIfPresent("market", java.util.Optional.ofNullable(market))
                        .build())
                .retrieve()
                .bodyToMono(AssetPriceResponse.class)
                .doOnError(e -> log.error("Error fetching spot price: {}", e.getMessage()))
                .onErrorResume(e -> Mono.empty()); // 에러 시 빈 결과 반환 (폴백은 호출 측에서 처리 가능)
    }
}
