package api.service.portfolio;

import api.domain.portfolio.PortfolioAiInsight;
import api.dto.portfolio.PortfolioAiInsightResponse;
import api.enums.portfolio.InsightStatus;
import api.exception.ResourceNotFoundException;
import api.repository.portfolio.PortfolioAiInsightRepository;
import api.repository.portfolio.PortfolioRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class PortfolioAiInsightService {

    private final PortfolioAiInsightRepository insightRepository;
    private final PortfolioRepository portfolioRepository;
    private final AiAdvisorServiceClient aiAdvisorServiceClient;

    /**
     * 포트폴리오의 최신 AI 분석 결과 조회
     */
    public Mono<PortfolioAiInsightResponse> getLatestInsight(UUID userId, UUID portfolioId) {
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
                .filter(portfolio -> portfolio.getUserId().equals(userId))
                .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
                .then(insightRepository.findFirstByPortfolioIdAndStatusOrderByAnalysisDateDesc(portfolioId,
                        InsightStatus.ACTIVE))
                .map(PortfolioAiInsightResponse::from);
    }

    /**
     * AI 분석 실행 요청
     */
    public Mono<Map<String, Object>> analyzePortfolio(UUID userId, UUID portfolioId) {
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
                .filter(portfolio -> portfolio.getUserId().equals(userId))
                .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
                .then(aiAdvisorServiceClient.analyzePortfolio(portfolioId));
    }
}
