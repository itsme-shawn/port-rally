package api.domain.terms;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

@Table("terms")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Terms {

    @Id
    @Column("terms_id")
    private UUID termsId;

    @Column("terms_type")
    private String termsType;  // SERVICE, PRIVACY, MARKETING, LOCATION, THIRD_PARTY

    @Column("title")
    private String title;

    @Column("content")
    private String content;

    @Column("is_required")
    @Builder.Default
    private Boolean isRequired = true;

    @Column("is_active")
    @Builder.Default
    private Boolean isActive = true;

    @Column("display_order")
    @Builder.Default
    private Integer displayOrder = 0;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    // Business methods
    public boolean isOptional() {
        return !isRequired;
    }
}
