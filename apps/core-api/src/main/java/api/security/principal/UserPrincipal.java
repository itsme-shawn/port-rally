package api.security.principal;

import api.enums.user.SocialProvider;
import lombok.Builder;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.OidcUserInfo;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Getter
@Builder
// SecurityContext에 보관되는 사용자 주체
public class UserPrincipal implements OidcUser {

    private UUID userId;
    private String email;
    private String displayName;
    private String profileImageUrl;
    private SocialProvider provider;

    @Builder.Default
    @Getter(lombok.AccessLevel.NONE)
    private Map<String, Object> attributes = new HashMap<>();

    // OIDC 관련 필드 (Google 등 OIDC provider용)
    @Getter(lombok.AccessLevel.NONE)
    private OidcIdToken idToken;
    @Getter(lombok.AccessLevel.NONE)
    private OidcUserInfo userInfo;

    @Override
    public Map<String, Object> getAttributes() {
        return attributes;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_USER"));
    }

    @Override
    public String getName() {
        return userId.toString();
    }

    @Override
    public Map<String, Object> getClaims() {
        return idToken != null ? idToken.getClaims() : Map.of();
    }

    @Override
    public OidcIdToken getIdToken() {
        return idToken;
    }

    @Override
    public OidcUserInfo getUserInfo() {
        return userInfo;
    }
}
