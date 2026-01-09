package api.dto.auth;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SignupCompleteResponse {

    private UUID userId;
    private String message;
    private Boolean success;

    public static SignupCompleteResponse success(UUID userId) {
        return SignupCompleteResponse.builder()
            .userId(userId)
            .message("회원가입이 완료되었습니다")
            .success(true)
            .build();
    }
}
