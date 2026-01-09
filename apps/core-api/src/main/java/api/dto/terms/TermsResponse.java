package api.dto.terms;

import api.domain.terms.Terms;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TermsResponse {

    private UUID termsId;
    private String termsType;
    private String title;
    private String content;
    private Boolean isRequired;
    private Integer displayOrder;

    public static TermsResponse from(Terms terms) {
        return TermsResponse.builder()
            .termsId(terms.getTermsId())
            .termsType(terms.getTermsType())
            .title(terms.getTitle())
            .content(terms.getContent())
            .isRequired(terms.getIsRequired())
            .displayOrder(terms.getDisplayOrder())
            .build();
    }
}
