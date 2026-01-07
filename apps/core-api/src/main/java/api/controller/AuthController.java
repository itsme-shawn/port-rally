package api.controller;

import api.dto.auth.AuthUserResponse;
import api.dto.auth.TokenResponse;
import api.exception.AuthException;
import api.security.jwt.JwtTokenProvider;
import api.security.principal.UserPrincipal;
import api.service.auth.AuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
// 인증/토큰 관련 API (헤더 기반 토큰 전달)
public class AuthController {

    private static final String REFRESH_TOKEN_HEADER = "X-Refresh-Token";

    private final AuthService authService;
    private final JwtTokenProvider jwtTokenProvider;

    @GetMapping("/me")
    public Mono<AuthUserResponse> getCurrentUser(@AuthenticationPrincipal UserPrincipal principal) {
        if (principal == null) {
            return Mono.error(new AuthException("Unauthorized"));
        }

        return authService.getCurrentUser(principal);
    }

    @PostMapping("/refresh")
    public Mono<TokenResponse> refresh(ServerWebExchange exchange) {
        String refreshToken = resolveRefreshToken(exchange);
        if (!StringUtils.hasText(refreshToken)) {
            return Mono.error(new AuthException("Refresh token not found"));
        }

		// refreshToken 을 받아서 access, refresh token (token pair) 재발급
        return authService.reIssueTokens(refreshToken)
            .map(tokens -> {
                var response = exchange.getResponse();
                var headers = response.getHeaders();
                var cookieConfig = jwtTokenProvider.getCookieConfig();

                // 헤더에도 설정 (API 클라이언트용)
                headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + tokens.accessToken());
                headers.set(REFRESH_TOKEN_HEADER, tokens.refreshToken());

                // access_token 쿠키 설정
                ResponseCookie.ResponseCookieBuilder accessTokenCookie = ResponseCookie
                    .from("access_token", tokens.accessToken())
                    .httpOnly(true)
                    .secure(cookieConfig.isSecure())
                    .path("/")
                    .maxAge(jwtTokenProvider.getAccessTokenExpiration() / 1000)
                    .sameSite(cookieConfig.getSameSite());

                if (StringUtils.hasText(cookieConfig.getDomain())) {
                    accessTokenCookie.domain(cookieConfig.getDomain());
                }
                response.addCookie(accessTokenCookie.build());

                // refresh_token 쿠키 설정 (Rotation)
                ResponseCookie.ResponseCookieBuilder refreshTokenCookie = ResponseCookie
                    .from("refresh_token", tokens.refreshToken())
                    .httpOnly(true)
                    .secure(cookieConfig.isSecure())
                    .path("/api/v1/auth/refresh")
                    .maxAge(jwtTokenProvider.getRefreshTokenExpiration() / 1000)
                    .sameSite(cookieConfig.getSameSite());

                if (StringUtils.hasText(cookieConfig.getDomain())) {
                    refreshTokenCookie.domain(cookieConfig.getDomain());
                }
                response.addCookie(refreshTokenCookie.build());

                log.info("Tokens refreshed successfully");

                return TokenResponse.of(tokens.accessToken(), jwtTokenProvider.getAccessTokenExpiration());
            });
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public Mono<Void> logout(
            @AuthenticationPrincipal UserPrincipal principal,
            ServerWebExchange exchange) {
        if (principal == null) {
            return Mono.error(new AuthException("Unauthorized"));
        }

        return authService.logout(principal.getUserId())
            .then(Mono.fromRunnable(() -> {
                var response = exchange.getResponse();
                var cookieConfig = jwtTokenProvider.getCookieConfig();

                // access_token 쿠키 삭제
                ResponseCookie.ResponseCookieBuilder accessTokenCookie = ResponseCookie
                    .from("access_token", "")
                    .httpOnly(true)
                    .secure(cookieConfig.isSecure())
                    .path("/")
                    .maxAge(0)
                    .sameSite(cookieConfig.getSameSite());

                if (StringUtils.hasText(cookieConfig.getDomain())) {
                    accessTokenCookie.domain(cookieConfig.getDomain());
                }
                response.addCookie(accessTokenCookie.build());

                // refresh_token 쿠키 삭제
                ResponseCookie.ResponseCookieBuilder refreshTokenCookie = ResponseCookie
                    .from("refresh_token", "")
                    .httpOnly(true)
                    .secure(cookieConfig.isSecure())
                    .path("/api/v1/auth/refresh")
                    .maxAge(0)
                    .sameSite(cookieConfig.getSameSite());

                if (StringUtils.hasText(cookieConfig.getDomain())) {
                    refreshTokenCookie.domain(cookieConfig.getDomain());
                }
                response.addCookie(refreshTokenCookie.build());

                log.info("User logged out: {}", principal.getEmail());
            }));
    }

    private String resolveRefreshToken(ServerWebExchange exchange) {
        // 헤더 우선, 없으면 쿠키로 fallback
        String headerToken = exchange.getRequest().getHeaders().getFirst(REFRESH_TOKEN_HEADER);
        if (StringUtils.hasText(headerToken)) {
            return headerToken;
        }

        HttpCookie cookie = exchange.getRequest().getCookies().getFirst("refresh_token");
        return cookie != null ? cookie.getValue() : null;
    }
}
