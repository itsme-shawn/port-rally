package api.controller;

import api.dto.auth.SignupCompleteRequest;
import api.dto.auth.SignupCompleteResponse;
import api.exception.AuthException;
import api.security.principal.UserPrincipal;
import api.service.auth.SignupService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "Signup", description = "회원가입 API")
public class SignupController {

    private final SignupService signupService;

    @PostMapping("/signup/complete")
    @ResponseStatus(HttpStatus.OK)
    @Operation(
        summary = "회원가입 완료",
        description = "약관 동의를 통해 회원가입을 완료합니다. PENDING 상태의 사용자만 호출 가능합니다."
    )
    public Mono<SignupCompleteResponse> completeSignup(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody SignupCompleteRequest request,
            ServerWebExchange exchange) {

        if (principal == null) {
            return Mono.error(new AuthException("Unauthorized"));
        }

        // 클라이언트 IP 주소 추출
        String ipAddress = extractIpAddress(exchange);

        // User-Agent 추출
        String userAgent = exchange.getRequest().getHeaders().getFirst("User-Agent");

        return signupService.completeSignup(
            principal.getUserId(),
            request,
            ipAddress,
            userAgent
        );
    }

    private String extractIpAddress(ServerWebExchange exchange) {
        // X-Forwarded-For 헤더 확인 (프록시/로드밸런서 뒤에 있을 경우)
        String forwardedFor = exchange.getRequest().getHeaders().getFirst("X-Forwarded-For");
        if (StringUtils.hasText(forwardedFor)) {
            return forwardedFor.split(",")[0].trim();
        }

        // X-Real-IP 헤더 확인
        String realIp = exchange.getRequest().getHeaders().getFirst("X-Real-IP");
        if (StringUtils.hasText(realIp)) {
            return realIp;
        }

        // Remote Address 사용
        var remoteAddress = exchange.getRequest().getRemoteAddress();
        return remoteAddress != null ? remoteAddress.getAddress().getHostAddress() : "unknown";
    }
}
