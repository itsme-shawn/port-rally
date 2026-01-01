package api.domain.ocr;

import api.enums.ocr.OcrStatus;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * AI가 이미지에서 추출한 OCR 결과
 */
@Table("ocr_results")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OcrResult {

    @Id
    @Column("ocr_result_id")
    private UUID ocrResultId;

    @Column("image_id")
    private UUID imageId;

    @Column("status")
    @Builder.Default
    private OcrStatus status = OcrStatus.PENDING;

    @Column("raw_text")
    private String rawText;

    @Column("parsed_data")
    private String parsedData;  // JSONB stored as String

    @CreatedDate
    @Column("created_at")
    private Instant createdAt;

    @LastModifiedDate
    @Column("updated_at")
    private Instant updatedAt;

    // Business methods
    public void verify() {
        this.status = OcrStatus.VERIFIED;
    }

    public void reject() {
        this.status = OcrStatus.REJECTED;
    }

    public void markFailed() {
        this.status = OcrStatus.FAILED;
    }
}
