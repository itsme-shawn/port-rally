package api.dto.quote;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 실시간 시세 스트리밍 DTO.
 * Redis Pub/Sub "quotes" 채널에서 수신하는 데이터 형식.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "실시간 시세 스트리밍 데이터")
public class QuoteStreamDto {

    @Schema(description = "종목 코드", example = "005930")
    private String symbol;

    @Schema(description = "국가 코드", example = "KR")
    private String national;

    @Schema(description = "거래소/시장", example = "KOSPI")
    private String exchange;

    @Schema(description = "제공자", example = "kis")
    private String provider;

    @Schema(description = "현재가", example = "167800")
    private BigDecimal price;

    @Schema(description = "전일 대비 변동", example = "300")
    private BigDecimal change;

    @Schema(description = "전일 대비 변동률 (%)", example = "0.18")
    @JsonProperty("change_rate")
    private BigDecimal changeRate;

    @Schema(description = "거래량", example = "13611702")
    private Long volume;

    @Schema(description = "시가", example = "163500")
    private BigDecimal open;

    @Schema(description = "고가", example = "168000")
    private BigDecimal high;

    @Schema(description = "저가", example = "163100")
    private BigDecimal low;

    @Schema(description = "타임스탬프", example = "2026-02-04T15:30:00")
    private String timestamp;

    @Schema(description = "업데이트 시각 (Unix timestamp)", example = "1707030000")
    @JsonProperty("updated_at")
    private Long updatedAt;

    /**
     * 식별자 생성 (national:exchange:symbol).
     */
    public String getIdentifier() {
        return String.format("%s:%s:%s", national, exchange, symbol);
    }
}
