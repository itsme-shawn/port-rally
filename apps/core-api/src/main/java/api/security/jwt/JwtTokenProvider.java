package api.security.jwt;

import api.config.JwtConfig;
import api.enums.user.SocialProvider;
import api.exception.AuthException;
import api.exception.TokenExpiredException;
import api.security.principal.UserPrincipal;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;

@Slf4j
@Component
// JWT 생성/검증 유틸리티
public class JwtTokenProvider {

    private final SecretKey secretKey;
    private final JwtConfig jwtConfig;

    public JwtTokenProvider(JwtConfig jwtConfig) {
        this.jwtConfig = jwtConfig;
        this.secretKey = Keys.hmacShaKeyFor(
            jwtConfig.getSecret().getBytes(StandardCharsets.UTF_8)
        );
    }

    /**
     * Access Token 생성
     */
    public String createAccessToken(UserPrincipal principal) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtConfig.getAccessTokenExpiration());

        return Jwts.builder()
            .subject(principal.getUserId().toString())
            .claim("email", principal.getEmail())
            .claim("displayName", principal.getDisplayName())
            .claim("profileImageUrl", principal.getProfileImageUrl())
            .claim("provider", principal.getProvider().name())
            .issuedAt(now)
            .expiration(expiry)
            .signWith(secretKey)
            .compact();
    }

    /**
     * Refresh Token 생성 (UUID 기반, Redis 저장용)
     */
    public String createRefreshToken() {
        return UUID.randomUUID().toString();
    }

    /**
     * Access Token 검증 및 Claims 추출
     */
    public Mono<Claims> validateAndGetClaims(String token) {
        return Mono.fromCallable(() ->
            Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload()
        ).onErrorResume(ExpiredJwtException.class, e -> {
            log.debug("Access token expired");
            return Mono.error(new TokenExpiredException("Access token expired"));
        }).onErrorResume(JwtException.class, e -> {
            log.warn("Invalid JWT token: {}", e.getMessage());
            return Mono.error(new AuthException("Invalid token"));
        });
    }

    /**
     * Claims에서 UserPrincipal 복원
     */
    public UserPrincipal getPrincipalFromClaims(Claims claims) {
        return UserPrincipal.builder()
            .userId(UUID.fromString(claims.getSubject()))
            .email(claims.get("email", String.class))
            .displayName(claims.get("displayName", String.class))
            .profileImageUrl(claims.get("profileImageUrl", String.class))
            .provider(SocialProvider.valueOf(claims.get("provider", String.class)))
            .build();
    }

    /**
     * Access Token TTL 반환 (밀리초)
     */
    public long getAccessTokenExpiration() {
        return jwtConfig.getAccessTokenExpiration();
    }

    /**
     * Refresh Token TTL 반환 (밀리초)
     */
    public long getRefreshTokenExpiration() {
        return jwtConfig.getRefreshTokenExpiration();
    }

    /**
     * Cookie 설정 반환
     */
    public JwtConfig.Cookie getCookieConfig() {
        return jwtConfig.getCookie();
    }
}
