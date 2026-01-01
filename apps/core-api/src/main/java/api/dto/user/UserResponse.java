package api.dto.user;

import api.domain.user.User;
import api.enums.user.UserStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserResponse {

    private UUID userId;
    private String displayName;
    private String email;
    private UserStatus status;
    private Instant createdAt;

    public static UserResponse from(User user) {
        return UserResponse.builder()
                .userId(user.getUserId())
                .displayName(user.getDisplayName())
                .email(user.getPrimaryEmail())
                .status(user.getStatus())
                .createdAt(user.getCreatedAt())
                .build();
    }
}
