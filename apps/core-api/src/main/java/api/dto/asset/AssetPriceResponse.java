package api.dto.asset;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AssetPriceResponse {
    private String symbol;
    private String national;
    private String exchange;
    private BigDecimal price;
    private BigDecimal change;

    @JsonProperty("change_rate")
    private BigDecimal changeRate;

    private Long volume;
    private BigDecimal high;
    private BigDecimal low;
    private BigDecimal open;

    @JsonProperty("raw_output")
    private Map<String, Object> rawOutput;
}
