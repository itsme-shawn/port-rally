package api.controller;

import api.dto.portfolio.AddPositionRequest;
import api.dto.portfolio.CreatePortfolioRequest;
import api.dto.portfolio.ImageUploadResponse;
import api.dto.portfolio.PortfolioCheckResponse;
import api.dto.portfolio.PortfolioResponse;
import api.dto.portfolio.PositionResponse;
import api.dto.portfolio.UpdatePortfolioRequest;
import api.exception.AuthException;
import api.security.principal.UserPrincipal;
import api.service.ocr.OcrService;
import api.service.portfolio.PortfolioService;
import api.service.portfolio.PositionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.codec.multipart.FilePart;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/portfolio")
@RequiredArgsConstructor
public class PortfolioController {

    private final PortfolioService portfolioService;
    private final PositionService positionService;
    private final OcrService ocrService;

    @Tag(name = "Portfolio")
    @GetMapping("/check")
    @Operation(
        summary = "포트폴리오 존재 여부 확인",
        description = "현재 로그인한 사용자의 포트폴리오 존재 여부를 확인합니다"
    )
    public Mono<PortfolioCheckResponse> checkPortfolio(
            @AuthenticationPrincipal UserPrincipal principal) {

        if (principal == null) {
            return Mono.error(new AuthException("Unauthorized"));
        }

        log.info("GET /api/v1/portfolio/check - userId: {}", principal.getUserId());

        return portfolioService.hasPortfolio(principal.getUserId())
            .map(hasPortfolio -> PortfolioCheckResponse.of(hasPortfolio));
    }

    @Tag(name = "Portfolio")
    @GetMapping
    @Operation(
        summary = "내 포트폴리오 목록 조회",
        description = "사용자의 모든 포트폴리오 목록을 조회합니다."
    )
    public Flux<PortfolioResponse> getPortfolios(
            @AuthenticationPrincipal UserPrincipal principal) {
        if (principal == null) return Flux.error(new AuthException("Unauthorized"));
        return portfolioService.getPortfolios(principal.getUserId());
    }

    @Tag(name = "Portfolio")
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(
        summary = "포트폴리오 생성",
        description = "새로운 포트폴리오를 생성합니다. (초기 자산 및 이미지 연결 가능)"
    )
    public Mono<PortfolioResponse> createPortfolio(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestBody @Valid CreatePortfolioRequest request) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return portfolioService.createPortfolio(principal.getUserId(), request);
    }

    @Tag(name = "Portfolio")
    @GetMapping("/{portfolioId}")
    @Operation(
        summary = "포트폴리오 상세 조회",
        description = "특정 포트폴리오의 상세 정보를 조회합니다."
    )
    public Mono<PortfolioResponse> getPortfolio(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID portfolioId) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return portfolioService.getPortfolio(principal.getUserId(), portfolioId);
    }

    @Tag(name = "Portfolio")
    @PatchMapping("/{portfolioId}")
    @Operation(
        summary = "포트폴리오 수정",
        description = "포트폴리오 정보를 수정합니다."
    )
    public Mono<PortfolioResponse> updatePortfolio(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID portfolioId,
            @RequestBody @Valid UpdatePortfolioRequest request) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return portfolioService.updatePortfolio(principal.getUserId(), portfolioId, request);
    }

    @Tag(name = "Portfolio")
    @DeleteMapping("/{portfolioId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(
        summary = "포트폴리오 삭제",
        description = "포트폴리오를 삭제합니다 (Soft Delete)."
    )
    public Mono<Void> deletePortfolio(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID portfolioId) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return portfolioService.deletePortfolio(principal.getUserId(), portfolioId);
    }

    // === Portfolio Setup 전용 API ===

    @Tag(name = "Portfolio Setup")
    @PostMapping(value = "/setup/upload-images", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(
        summary = "포트폴리오 셋업용 OCR 이미지 분석",
        description = "포트폴리오 생성 전에 이미지를 업로드하여 종목 정보를 추출합니다."
    )
    public Flux<ImageUploadResponse> setupUploadImages(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestPart("files") Flux<FilePart> files) {

        if (principal == null) return Flux.error(new AuthException("Unauthorized"));
        log.info("POST /api/v1/portfolio/setup/upload-images - userId: {}", principal.getUserId());

        return files.flatMap(file -> 
            ocrService.uploadAnalyzeAndGetResult(principal.getUserId(), null, file)
        );
    }

    @Tag(name = "Portfolio Setup")
    @PostMapping("/setup/manual")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(
        summary = "포트폴리오 셋업용 자산 수기 추가",
        description = "이미 생성된 포트폴리오에 초기 자산 포지션을 수기로 추가합니다. 요청 바디에 portfolioId를 포함해야 합니다."
    )
    public Mono<PositionResponse> setupManualEntry(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestBody @Valid AddPositionRequest request) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return positionService.addPosition(principal.getUserId(), request.portfolioId(), request);
    }
}