package api.controller;

import api.dto.portfolio.PortfolioAiInsightResponse;
import api.security.principal.UserPrincipal;
import api.service.portfolio.PortfolioAiInsightService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/portfolio/{portfolioId}/ai")
@RequiredArgsConstructor
@Tag(name = "Portfolio AI", description = "포트폴리오 AI 분석 관련 API")
public class PortfolioAiInsightController {

    private final PortfolioAiInsightService insightService;

    @GetMapping("/latest")
    @Operation(summary = "최신 AI 분석 결과 조회", description = "특정 포트폴리오의 가장 최근 활성화된 AI 분석 리포트를 조회합니다.")
    public Mono<PortfolioAiInsightResponse> getLatestInsight(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID portfolioId) {
        log.info("GET /api/v1/portfolio/{}/ai/latest - userId: {}", portfolioId, principal.getUserId());
        return insightService.getLatestInsight(principal.getUserId(), portfolioId);
    }

    @PostMapping("/analyze")
    @Operation(summary = "AI 분석 실행", description = "AI Advisor에게 포트폴리오 분석을 요청합니다. 분석은 비동기로 진행됩니다.")
    public Mono<Map<String, Object>> analyzePortfolio(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID portfolioId) {
        log.info("POST /api/v1/portfolio/{}/ai/analyze - userId: {}", portfolioId, principal.getUserId());
        return insightService.analyzePortfolio(principal.getUserId(), portfolioId);
    }
}
