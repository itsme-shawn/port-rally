package api.security.handler;

import api.security.jwt.JwtTokenProvider;
import api.security.principal.UserPrincipal;
import api.service.auth.RefreshTokenService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.server.WebFilterExchange;
import org.springframework.security.web.server.authentication.ServerAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.net.URI;
import java.time.Duration;

@Slf4j
@Component
@RequiredArgsConstructor
// OAuth2 성공 시 access/refresh 토큰 발급 후 리다이렉트 처리
public class OAuth2AuthenticationSuccessHandler implements ServerAuthenticationSuccessHandler {

    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;

    @Value("${oauth2.success-redirect-uri}")
    private String successRedirectUri;

    @Override
    public Mono<Void> onAuthenticationSuccess(WebFilterExchange webFilterExchange,
            Authentication authentication) {

        UserPrincipal principal = (UserPrincipal) authentication.getPrincipal();

        String accessToken = jwtTokenProvider.createAccessToken(principal);
        String refreshToken = jwtTokenProvider.createRefreshToken();

        log.info("OAuth2 authentication success for user: {}", principal.getEmail());

        return refreshTokenService
            .saveRefreshToken(principal.getUserId(), refreshToken) // refresh token 발급
            .then(Mono.fromRunnable(() -> {
                var response = webFilterExchange.getExchange().getResponse();
                var headers = response.getHeaders();
                headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
                headers.set("X-Refresh-Token", refreshToken);

                var cookieConfig = jwtTokenProvider.getCookieConfig();

                // Refresh Token 쿠키 발급 (httpOnly로 보안 강화)
                ResponseCookie.ResponseCookieBuilder refreshTokenBuilder = ResponseCookie
                    .from("refresh_token", refreshToken)
                    .httpOnly(true)
                    .secure(cookieConfig.isSecure())
                    .path("/api/v1/auth/refresh")
                    .maxAge(Duration.ofMillis(jwtTokenProvider.getRefreshTokenExpiration()))
                    .sameSite(cookieConfig.getSameSite());

                if (org.springframework.util.StringUtils.hasText(cookieConfig.getDomain())) {
                    refreshTokenBuilder.domain(cookieConfig.getDomain());
                }

                response.addCookie(refreshTokenBuilder.build());

                // Access Token 쿠키 발급 (httpOnly로 보안 강화)
                // 클라이언트는 /api/v1/auth/me로 사용자 정보 조회
                ResponseCookie.ResponseCookieBuilder accessTokenBuilder = ResponseCookie
                    .from("access_token", accessToken)
                    .httpOnly(true)
                    .secure(cookieConfig.isSecure())
                    .path("/")
                    .maxAge(Duration.ofMillis(jwtTokenProvider.getAccessTokenExpiration()))
                    .sameSite(cookieConfig.getSameSite());

                if (org.springframework.util.StringUtils.hasText(cookieConfig.getDomain())) {
                    accessTokenBuilder.domain(cookieConfig.getDomain());
                }

                response.addCookie(accessTokenBuilder.build());

                // 프론트엔드로 리다이렉트
                response.setStatusCode(HttpStatus.FOUND);
                response.getHeaders().setLocation(URI.create(successRedirectUri));
            }));
    }
}
