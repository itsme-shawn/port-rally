package api.security.oauth2;

import api.enums.user.SocialProvider;

import java.util.Map;

// Google OAuth2 사용자 정보 매핑
public class GoogleOAuth2UserInfo extends OAuth2UserInfo {

    public GoogleOAuth2UserInfo(Map<String, Object> attributes) {
        super(attributes);
    }

    @Override
    public String getProviderId() {
        return (String) attributes.get("sub");
    }

    @Override
    public String getEmail() {
        return (String) attributes.get("email");
    }

    @Override
    public String getName() {
        return (String) attributes.get("name");
    }

    @Override
    public String getImageUrl() {
        return (String) attributes.get("picture");
    }

    @Override
    public boolean isEmailVerified() {
        return Boolean.TRUE.equals(attributes.get("email_verified"));
    }

    @Override
    public SocialProvider getProvider() {
        return SocialProvider.GOOGLE;
    }
}
