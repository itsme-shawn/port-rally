package api.dto.auth;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
// Access Token 응답 포맷
public class TokenResponse {

    private String accessToken;
    private long expiresIn;
    private String tokenType;

    public static TokenResponse of(String accessToken, long expiresIn) {
        return TokenResponse.builder()
            .accessToken(accessToken)
            .expiresIn(expiresIn)
            .tokenType("Bearer")
            .build();
    }
}
