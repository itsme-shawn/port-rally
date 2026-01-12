package api.domain.terms;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

@Table("user_terms_agreements")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserTermsAgreement {

    @Id
    @Column("agreement_id")
    private UUID agreementId;

    @Column("user_id")
    private UUID userId;

    @Column("terms_id")
    private Long termsId;

    @Column("agreed")
    @Builder.Default
    private Boolean agreed = true;

    @Column("agreed_at")
    private Instant agreedAt;

    @Column("ip_address")
    private String ipAddress;

    @Column("user_agent")
    private String userAgent;
}
