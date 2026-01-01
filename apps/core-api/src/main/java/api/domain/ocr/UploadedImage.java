package api.domain.ocr;

import api.enums.ocr.UploadStatus;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * 사용자가 업로드한 계좌 이미지
 */
@Table("uploaded_images")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UploadedImage {

    @Id
    @Column("image_id")
    private UUID imageId;

    @Column("user_id")
    private UUID userId;

    @Column("portfolio_id")
    private UUID portfolioId;

    @Column("storage_url")
    private String storageUrl;

    @Column("upload_status")
    @Builder.Default
    private UploadStatus uploadStatus = UploadStatus.PENDING;

    @Column("content_type")
    private String contentType;

    @Column("file_size")
    private Long fileSize;

    @Column("hash_sha256")
    private String hashSha256;

    @Column("retention_policy")
    @Builder.Default
    private String retentionPolicy = "90_DAYS";

    @Column("retain_until")
    private Instant retainUntil;

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    // Business methods
    public void markProcessing() {
        this.uploadStatus = UploadStatus.PROCESSING;
    }

    public void markCompleted() {
        this.uploadStatus = UploadStatus.COMPLETED;
    }

    public void markFailed() {
        this.uploadStatus = UploadStatus.FAILED;
    }
}
