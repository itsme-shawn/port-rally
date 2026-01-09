package api.service.auth;

import api.config.JwtConfig;
import api.exception.AuthException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
// Redis에 Refresh 토큰을 저장/검증/갱신하는 서비스
public class RefreshTokenService {

    private static final String REFRESH_TOKEN_PREFIX = "refresh_token:";
    private static final String USER_TOKEN_PREFIX = "user_refresh:";

    private final ReactiveRedisTemplate<String, String> redisTemplate;
    private final JwtConfig jwtConfig;

    /**
     * Refresh Token 저장
     * - refresh_token:{token} -> userId (토큰 재발급 시, 사용자 검증용)
     * - user_refresh:{userId} -> token (사용자별 단일 토큰 저장/삭제) => 단일기기로만 로그인 허용 됨
     */
    public Mono<Void> saveRefreshToken(UUID userId, String refreshToken) {
        Duration ttl = Duration.ofMillis(jwtConfig.getRefreshTokenExpiration());
        String userIdStr = userId.toString();

        return redisTemplate.opsForValue()
            // 기존 토큰 삭제 (단일 세션 유지)
            .get(USER_TOKEN_PREFIX + userIdStr)
            .flatMap(oldToken -> redisTemplate.delete(REFRESH_TOKEN_PREFIX + oldToken))
            // 새 토큰 저장
            .then(redisTemplate.opsForValue()
                .set(REFRESH_TOKEN_PREFIX + refreshToken, userIdStr, ttl))
            .then(redisTemplate.opsForValue()
                .set(USER_TOKEN_PREFIX + userIdStr, refreshToken, ttl))
            .doOnSuccess(v -> log.debug("Refresh token saved for user: {}", userIdStr))
            .then();
    }

    /**
     * Refresh Token 검증 및 userId 반환
     */
    public Mono<UUID> validateRefreshToken(String refreshToken) {
        return redisTemplate.opsForValue()
            .get(REFRESH_TOKEN_PREFIX + refreshToken)
            .map(UUID::fromString)
            .switchIfEmpty(Mono.error(new AuthException("Invalid refresh token")));
    }

    /**
     * Refresh Token 삭제 (로그아웃)
     */
    public Mono<Void> deleteRefreshToken(UUID userId) {
        String userIdStr = userId.toString();

        return redisTemplate.opsForValue()
            .get(USER_TOKEN_PREFIX + userIdStr)
            .flatMap(token -> redisTemplate.delete(REFRESH_TOKEN_PREFIX + token))
            .then(redisTemplate.delete(USER_TOKEN_PREFIX + userIdStr))
            .doOnSuccess(v -> log.debug("Refresh token deleted for user: {}", userIdStr))
            .then();
    }

    /**
     * 토큰 갱신 (Rotation)
     */
    public Mono<String> rotateRefreshToken(UUID userId, String oldRefreshToken, String newRefreshToken) {
        return deleteRefreshToken(userId)
            .then(saveRefreshToken(userId, newRefreshToken))
            .thenReturn(newRefreshToken);
    }
}
