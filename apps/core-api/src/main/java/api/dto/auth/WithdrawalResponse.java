package api.dto.auth;

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
public class WithdrawalResponse {

    private UUID userId;
    private String message;
    private Instant withdrawnAt;

    public static WithdrawalResponse success(UUID userId) {
        return WithdrawalResponse.builder()
            .userId(userId)
            .message("회원 탈퇴가 완료되었습니다")
            .withdrawnAt(Instant.now())
            .build();
    }
}
