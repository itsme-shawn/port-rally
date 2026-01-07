package api.security.jwt;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.security.core.context.SecurityContextImpl;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Slf4j
@Component
@RequiredArgsConstructor
// Authorization 헤더 또는 쿠키의 Bearer 토큰을 검증해 인증 컨텍스트에 주입
public class JwtAuthenticationFilter implements WebFilter {

    private static final String BEARER_PREFIX = "Bearer ";
    private static final String ACCESS_TOKEN_COOKIE = "access_token";

    private final JwtTokenProvider jwtTokenProvider;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        String token = resolveToken(exchange);

        if (!StringUtils.hasText(token)) {
            log.debug("No token found for path: {}", path);
            return chain.filter(exchange);
        }

        log.debug("Token found for path: {}, token length: {}", path, token.length());

        return jwtTokenProvider.validateAndGetClaims(token)
            .map(jwtTokenProvider::getPrincipalFromClaims)
            .doOnNext(principal -> log.debug("JWT validated for user: {}", principal.getEmail()))
            .map(principal -> new UsernamePasswordAuthenticationToken(
                principal, token, principal.getAuthorities()))
            .map(SecurityContextImpl::new)
            .flatMap(context -> chain.filter(exchange)
                .contextWrite(ReactiveSecurityContextHolder.withSecurityContext(Mono.just(context))))
            .onErrorResume(ex -> {
                log.warn("JWT authentication failed for path {}: {}", path, ex.getMessage());
                return chain.filter(exchange);
            });
    }

    private String resolveToken(ServerWebExchange exchange) {
        // 1. Authorization 헤더 우선
        String authHeader = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(authHeader) && authHeader.startsWith(BEARER_PREFIX)) {
            log.debug("Token found in Authorization header");
            return authHeader.substring(BEARER_PREFIX.length());
        }

        // 2. 쿠키에서 access_token 조회 (httpOnly 쿠키 지원)
        HttpCookie cookie = exchange.getRequest().getCookies().getFirst(ACCESS_TOKEN_COOKIE);
        if (cookie != null && StringUtils.hasText(cookie.getValue())) {
            log.debug("Token found in cookie");
            return cookie.getValue();
        }

        // 디버깅: 쿠키 목록 출력
        var cookies = exchange.getRequest().getCookies();
        if (!cookies.isEmpty()) {
            log.debug("Available cookies: {}", cookies.keySet());
        }

        return null;
    }
}
