package api.controller;

import api.dto.terms.TermsResponse;
import api.service.terms.TermsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@Slf4j
@RestController
@RequestMapping("/api/v1/terms")
@RequiredArgsConstructor
@Tag(name = "Terms", description = "약관 API")
public class TermsController {

    private final TermsService termsService;

    @GetMapping
    @Operation(
        summary = "약관 목록 조회",
        description = "현재 유효한 약관 목록을 표시 순서대로 조회합니다"
    )
    public Flux<TermsResponse> getActiveTerms() {
        return termsService.getActiveTerms();
    }
}
