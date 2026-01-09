package api.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

// JWT 설정 값을 바인딩하는 프로퍼티 클래스
@Component
@ConfigurationProperties(prefix = "jwt") // @Value 없이 application.yml 로부터 값 매핑시켜줌
@Getter
@Setter
public class JwtConfig {

	// application.yml kebab-case => springboot camelCase
	// access-token-expiration => accessTokenExpiration 로 변환

    private String secret;
    private long accessTokenExpiration;   // 15분 (밀리초)
    private long refreshTokenExpiration;  // 7일 (밀리초)
    private Cookie cookie = new Cookie();

    @Getter
    @Setter
    public static class Cookie {
        private String domain;
        private boolean secure;
        private String sameSite = "Lax";
    }
}
