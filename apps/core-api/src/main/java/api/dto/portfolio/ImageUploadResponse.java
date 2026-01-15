package api.dto.portfolio;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 이미지 업로드 및 OCR 분석 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "이미지 업로드 및 OCR 분석 결과")
public class ImageUploadResponse {

    @Schema(description = "OCR 결과 ID", example = "123e4567-e89b-12d3-a456-426614174001")
    private UUID ocrResultId;

    @Schema(description = "감지된 종목 목록")
    private List<DetectedPositionDto> detectedPositions;

    /**
     * 응답 생성 헬퍼 메서드
     */
    public static ImageUploadResponse of(UUID ocrResultId, List<DetectedPositionDto> detectedPositions) {
        return ImageUploadResponse.builder()
            .ocrResultId(ocrResultId)
            .detectedPositions(detectedPositions)
            .build();
    }
}
