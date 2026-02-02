package api.redis;

/**
 * Redis key 생성 헬퍼 클래스.
 *
 * redis-meta.yml 스키마를 기반으로 타입 안전한 키를 생성합니다.
 */
public class RedisKeys {

    // Refresh token 키: refresh_token:{token}
    public static String refreshToken(String token) {
        return "refresh_token:" + token;
    }

    // User refresh 키: user_refresh:{userId}
    public static String userRefresh(String userId) {
        return "user_refresh:" + userId;
    }

    // TTL 값 (milliseconds)
    public static class TTL {
        public static final long REFRESH_TOKEN = 604800000L; // 7일
        public static final long USER_REFRESH = 604800000L;  // 7일
    }
}
