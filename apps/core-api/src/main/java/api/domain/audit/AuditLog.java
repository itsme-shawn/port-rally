package api.domain.audit;

import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 사용자 활동 감사 로그
 */
@Table("audit_logs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuditLog {

    @Id
    @Column("audit_log_id")
    private Long auditLogId;

    @Column("user_id")
    private UUID userId;

    @Column("event_type")
    private String eventType;

    @Column("metadata")
    private String metadata;  // JSONB stored as String

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    // Factory methods for common events
    public static AuditLog login(UUID userId) {
        return AuditLog.builder()
                .userId(userId)
                .eventType("LOGIN")
                .build();
    }

    public static AuditLog linkSocial(UUID userId, String provider) {
        return AuditLog.builder()
                .userId(userId)
                .eventType("LINK_SOCIAL")
                .metadata("{\"provider\": \"" + provider + "\"}")
                .build();
    }

    public static AuditLog portfolioCreate(UUID userId, UUID portfolioId) {
        return AuditLog.builder()
                .userId(userId)
                .eventType("PORTFOLIO_CREATE")
                .metadata("{\"portfolio_id\": \"" + portfolioId + "\"}")
                .build();
    }

    public static AuditLog imageUpload(UUID userId, UUID imageId) {
        return AuditLog.builder()
                .userId(userId)
                .eventType("IMAGE_UPLOAD")
                .metadata("{\"image_id\": \"" + imageId + "\"}")
                .build();
    }

    public static AuditLog positionAdd(UUID userId, UUID portfolioId, UUID assetId) {
        return AuditLog.builder()
                .userId(userId)
                .eventType("POSITION_ADD")
                .metadata("{\"portfolio_id\": \"" + portfolioId + "\", \"asset_id\": \"" + assetId + "\"}")
                .build();
    }
}
