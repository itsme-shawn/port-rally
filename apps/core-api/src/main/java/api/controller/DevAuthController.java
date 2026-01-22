package api.controller;

import api.domain.user.SocialAccount;
import api.domain.user.User;
import api.dto.auth.DevTokenRequest;
import api.dto.auth.TokenResponse;
import api.exception.AuthException;
import api.repository.user.SocialAccountRepository;
import api.repository.user.UserRepository;
import api.security.jwt.JwtTokenProvider;
import api.security.principal.UserPrincipal;
import api.service.auth.RefreshTokenService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.time.Duration;

// ⚠️ 개발용 컨트롤러 - local 환경에서만 활성화됨
// Swagger에서 쿠키 기반 인증 테스트를 위한 간편 토큰 발급 API
@Slf4j
@Profile({"local", "remote"})
@RestController
@RequestMapping("/api/v1/auth/dev")
@RequiredArgsConstructor
@Tag(name = "Dev Auth", description = "⚠️ 개발용 인증 API (local 환경에서만 사용 가능)")
public class DevAuthController {

    private final UserRepository userRepository;
    private final SocialAccountRepository socialAccountRepository;
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;

    // ⚠️ 개발용 - 이메일로 사용자 조회 후 쿠키에 토큰 자동 설정
    @PostMapping("/token")
    @Operation(
        summary = "⚠️ [개발용] 토큰 발급",
        description = "이메일로 사용자를 조회하여 access_token과 refresh_token을 쿠키에 설정합니다. " +
            "Swagger UI에서 이 API를 호출하면 이후 모든 요청에 자동으로 쿠키가 포함됩니다. (local 환경 전용)"
    )
    public Mono<TokenResponse> issueDevToken(
            @Valid @RequestBody DevTokenRequest request,
            ServerWebExchange exchange) {

        // 개발용: 이메일로 사용자 조회 (실제 환경에서는 이런 방식 절대 금지!)
        return userRepository.findByPrimaryEmail(request.email())
            .filter(user -> user.getDeletedAt() == null)
            .switchIfEmpty(Mono.error(new AuthException("User not found with email: " + request.email())))
            .flatMap(user -> socialAccountRepository
                .findAllByUserIdAndIsActiveTrue(user.getUserId())
                .next()
                .switchIfEmpty(Mono.error(new AuthException("No active social account found")))
                .map(socialAccount -> createPrincipal(user, socialAccount))
            )
            .flatMap(principal -> {
                String accessToken = jwtTokenProvider.createAccessToken(principal);
                String refreshToken = jwtTokenProvider.createRefreshToken();

                log.info("⚠️ [DEV] Token issued for user: {}", principal.getEmail());

                return refreshTokenService
                    .saveRefreshToken(principal.getUserId(), refreshToken)
                    .thenReturn(principal)
                    .map(p -> {
                        setTokenCookies(exchange, accessToken, refreshToken);
                        return TokenResponse.of(accessToken, jwtTokenProvider.getAccessTokenExpiration());
                    });
            });
    }

    private UserPrincipal createPrincipal(User user, SocialAccount socialAccount) {
        return UserPrincipal.builder()
            .userId(user.getUserId())
            .email(user.getPrimaryEmail())
            .displayName(user.getDisplayName())
            .profileImageUrl(user.getProfileImageUrl())
            .provider(socialAccount.getProvider())
            .build();
    }

    private void setTokenCookies(ServerWebExchange exchange, String accessToken, String refreshToken) {
        var response = exchange.getResponse();
        var headers = response.getHeaders();
        var cookieConfig = jwtTokenProvider.getCookieConfig();

        // 헤더에도 설정 (API 클라이언트용)
        headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
        headers.set("X-Refresh-Token", refreshToken);

        // Access Token 쿠키 설정
        ResponseCookie.ResponseCookieBuilder accessTokenBuilder = ResponseCookie
            .from("access_token", accessToken)
            .httpOnly(true)
            .secure(cookieConfig.isSecure())
            .path("/")
            .maxAge(Duration.ofMillis(jwtTokenProvider.getAccessTokenExpiration()))
            .sameSite(cookieConfig.getSameSite());

        if (StringUtils.hasText(cookieConfig.getDomain())) {
            accessTokenBuilder.domain(cookieConfig.getDomain());
        }
        response.addCookie(accessTokenBuilder.build());

        // Refresh Token 쿠키 설정
        ResponseCookie.ResponseCookieBuilder refreshTokenBuilder = ResponseCookie
            .from("refresh_token", refreshToken)
            .httpOnly(true)
            .secure(cookieConfig.isSecure())
            .path("/api/v1/auth/refresh")
            .maxAge(Duration.ofMillis(jwtTokenProvider.getRefreshTokenExpiration()))
            .sameSite(cookieConfig.getSameSite());

        if (StringUtils.hasText(cookieConfig.getDomain())) {
            refreshTokenBuilder.domain(cookieConfig.getDomain());
        }
        response.addCookie(refreshTokenBuilder.build());
    }

    // ⚠️ 개발용 - 현재 인증된 사용자의 토큰을 JSON으로 반환 (Codespace 쿠키 동기화용)
    @PostMapping("/current-token")
    @Operation(
        summary = "⚠️ [개발용] 현재 세션 토큰 조회",
        description = "현재 인증된 사용자의 access_token과 refresh_token을 JSON으로 반환합니다. " +
            "Remote 개발환경에서 포트별 쿠키 공유 문제 해결용 (local 환경 전용)"
    )
    public Mono<java.util.Map<String, String>> getCurrentToken(ServerWebExchange exchange) {
        return exchange.getPrincipal()
            .cast(org.springframework.security.core.Authentication.class)
            .map(auth -> (UserPrincipal) auth.getPrincipal())
            .flatMap(principal -> {
                String accessToken = jwtTokenProvider.createAccessToken(principal);
                String refreshToken = jwtTokenProvider.createRefreshToken();

                log.info("⚠️ [DEV] Current token requested for user: {}", principal.getEmail());

                return refreshTokenService
                    .saveRefreshToken(principal.getUserId(), refreshToken)
                    .thenReturn(java.util.Map.of(
                        "accessToken", accessToken,
                        "refreshToken", refreshToken
                    ));
            })
            .switchIfEmpty(Mono.error(new AuthException("Not authenticated")));
    }
}
