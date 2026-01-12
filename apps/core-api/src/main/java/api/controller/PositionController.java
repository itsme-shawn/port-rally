package api.controller;

import api.dto.portfolio.PositionResponse;
import api.dto.portfolio.UpdatePositionRequest;
import api.exception.AuthException;
import api.security.principal.UserPrincipal;
import api.service.portfolio.PositionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class PositionController {

    private final PositionService positionService;

    @Tag(name = "Position")
    @GetMapping("/portfolio/{portfolioId}/positions")
    @Operation(
        summary = "포지션 목록 조회",
        description = "특정 포트폴리오의 모든 포지션 목록을 조회합니다."
    )
    public Flux<PositionResponse> getPositions(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID portfolioId) {
        if (principal == null) return Flux.error(new AuthException("Unauthorized"));
        return positionService.getPositions(principal.getUserId(), portfolioId);
    }

    @Tag(name = "Position")
    @PatchMapping("/positions/{positionId}")
    @Operation(
        summary = "포지션 수정",
        description = "보유 포지션 정보를 수정합니다."
    )
    public Mono<PositionResponse> updatePosition(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID positionId,
            @RequestBody @Valid UpdatePositionRequest request) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return positionService.updatePosition(principal.getUserId(), positionId, request);
    }

    @Tag(name = "Position")
    @DeleteMapping("/positions/{positionId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(
        summary = "포지션 삭제",
        description = "보유 포지션을 삭제합니다 (Soft Delete)."
    )
    public Mono<Void> deletePosition(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID positionId) {
        if (principal == null) return Mono.error(new AuthException("Unauthorized"));
        return positionService.deletePosition(principal.getUserId(), positionId);
    }
}
