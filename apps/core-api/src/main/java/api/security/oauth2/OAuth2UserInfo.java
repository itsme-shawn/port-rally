package api.security.oauth2;

import api.enums.user.SocialProvider;
import lombok.Getter;

import java.util.Map;

@Getter
// OAuth2 사용자 속성 추상화
public abstract class OAuth2UserInfo {

    protected Map<String, Object> attributes;

    protected OAuth2UserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    public abstract String getProviderId();

    public abstract String getEmail();

    public abstract String getName();

    public abstract String getImageUrl();

    public abstract boolean isEmailVerified();

    public abstract SocialProvider getProvider();

    /**
     * Provider별 OAuth2UserInfo 팩토리 메서드
     * Apple 등 추가 시 이 메서드에 case 추가
     */
    public static OAuth2UserInfo of(String registrationId, Map<String, Object> attributes) {
        return switch (registrationId.toLowerCase()) {
            case "google" -> new GoogleOAuth2UserInfo(attributes);
            // case "apple" -> new AppleOAuth2UserInfo(attributes);
            default -> throw new IllegalArgumentException("Unsupported provider: " + registrationId);
        };
    }
}
