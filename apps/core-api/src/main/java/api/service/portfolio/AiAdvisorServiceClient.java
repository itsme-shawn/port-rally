package api.service.portfolio;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
public class AiAdvisorServiceClient {

    private final WebClient webClient;

    public AiAdvisorServiceClient(
            WebClient.Builder webClientBuilder,
            @Value("${app.ai-advisor.base-url}") String baseUrl) {
        this.webClient = webClientBuilder.baseUrl(baseUrl).build();
    }

    /**
     * AI Advisor 서비스에 포트폴리오 분석을 요청합니다.
     */
    public Mono<Map<String, Object>> analyzePortfolio(UUID portfolioId) {
        log.info("Requesting portfolio analysis for portfolioId: {}", portfolioId);

        return webClient.post()
                .uri("/v1/analyze/portfolio/{portfolioId}", portfolioId)
                .retrieve()
                .bodyToMono(Map.class)
                .map(res -> (Map<String, Object>) res)
                .doOnSuccess(res -> log.info("Successfully requested portfolio analysis for {}: {}", portfolioId, res))
                .doOnError(
                        e -> log.error("Error requesting portfolio analysis for {}: {}", portfolioId, e.getMessage()));
    }
}
