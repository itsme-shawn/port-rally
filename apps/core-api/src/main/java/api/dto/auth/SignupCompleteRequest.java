package api.dto.auth;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SignupCompleteRequest {

    @NotEmpty(message = "약관 동의 정보는 필수입니다")
    @Valid
    private List<TermsAgreementItem> agreements;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TermsAgreementItem {

        @NotNull(message = "약관 ID는 필수입니다")
        private Long termsId;

        @NotNull(message = "동의 여부는 필수입니다")
        private Boolean agreed;
    }
}
