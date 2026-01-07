package api.dto.auth;

import api.domain.user.User;
import api.enums.user.SocialProvider;
import api.enums.user.UserStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
// 인증된 사용자 정보 응답 DTO
public class AuthUserResponse {

    private UUID userId;
    private String email;
    private String displayName;
    private String profileImageUrl;
    private SocialProvider provider;
    private UserStatus status;

    public static AuthUserResponse from(User user, SocialProvider provider) {
        return AuthUserResponse.builder()
            .userId(user.getUserId())
            .email(user.getPrimaryEmail())
            .displayName(user.getDisplayName())
            .profileImageUrl(user.getProfileImageUrl())
            .provider(provider)
            .status(user.getStatus())
            .build();
    }
}
