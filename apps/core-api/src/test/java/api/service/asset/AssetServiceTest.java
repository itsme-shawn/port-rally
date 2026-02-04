package api.service.asset;

import api.domain.asset.Asset;
import api.dto.asset.AssetDetailResponse;
import api.dto.asset.AssetPriceResponse;
import api.exception.ResourceNotFoundException;
import api.repository.asset.AssetRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.math.BigDecimal;
import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AssetServiceTest {

    @Mock
    private AssetRepository assetRepository;

    @Mock
    private MarketDataServiceClient marketDataServiceClient;

    @InjectMocks
    private AssetService assetService;

    private Asset testAsset;
    private AssetPriceResponse testPriceResponse;

    @BeforeEach
    void setUp() {
        testAsset = Asset.builder()
                .assetId(1L)
                .national("KR")
                .market("KRX")
                .symbol("005930")
                .isin("KR7005930003")
                .nameKo("삼성전자")
                .nameEn("Samsung Electronics")
                .assetType("STOCK")
                .currency("KRW")
                .sectorScheme("GICS")
                .sectorTags(new String[]{"Technology", "Semiconductor"})
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();

        testPriceResponse = AssetPriceResponse.builder()
                .symbol("005930")
                .national("KR")
                .exchange("KRX")
                .price(new BigDecimal("75000"))
                .change(new BigDecimal("1000"))
                .changeRate(new BigDecimal("1.35"))
                .volume(15000000L)
                .build();
    }

    @Test
    @DisplayName("includePrice=false: 가격 정보 없이 자산 상세 조회")
    void testGetAssetDetailsBySymbolIdentifier_WithoutPrice() {
        // given
        String identifier = "KR:KRX:005930";
        when(assetRepository.findByNationalAndMarketAndSymbol("KR", "KRX", "005930"))
                .thenReturn(Mono.just(testAsset));

        // when
        Mono<AssetDetailResponse> result = assetService.getAssetDetailsBySymbolIdentifier(identifier, false);

        // then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertThat(response).isNotNull();
                    assertThat(response.identifier()).isEqualTo("KR:KRX:005930");
                    assertThat(response.symbol()).isEqualTo("005930");
                    assertThat(response.nameKo()).isEqualTo("삼성전자");
                    assertThat(response.price()).isNull(); // 가격 정보는 null이어야 함
                })
                .verifyComplete();

        verify(assetRepository, times(1))
                .findByNationalAndMarketAndSymbol("KR", "KRX", "005930");
        verify(marketDataServiceClient, never()).getSpotPrice(anyString(), anyString(), anyString());
    }

    @Test
    @DisplayName("includePrice=true: 가격 정보 포함하여 자산 상세 조회 성공")
    void testGetAssetDetailsBySymbolIdentifier_WithPrice_Success() {
        // given
        String identifier = "KR:KRX:005930";
        when(assetRepository.findByNationalAndMarketAndSymbol("KR", "KRX", "005930"))
                .thenReturn(Mono.just(testAsset));
        when(marketDataServiceClient.getSpotPrice("005930", "KR", "KRX"))
                .thenReturn(Mono.just(testPriceResponse));

        // when
        Mono<AssetDetailResponse> result = assetService.getAssetDetailsBySymbolIdentifier(identifier, true);

        // then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertThat(response).isNotNull();
                    assertThat(response.identifier()).isEqualTo("KR:KRX:005930");
                    assertThat(response.symbol()).isEqualTo("005930");
                    assertThat(response.nameKo()).isEqualTo("삼성전자");
                    assertThat(response.price()).isNotNull(); // 가격 정보가 있어야 함
                    assertThat(response.price().getPrice()).isEqualByComparingTo("75000");
                    assertThat(response.price().getChange()).isEqualByComparingTo("1000");
                    assertThat(response.price().getChangeRate()).isEqualByComparingTo("1.35");
                })
                .verifyComplete();

        verify(assetRepository, times(1))
                .findByNationalAndMarketAndSymbol("KR", "KRX", "005930");
        verify(marketDataServiceClient, times(1))
                .getSpotPrice("005930", "KR", "KRX");
    }

    @Test
    @DisplayName("includePrice=true: market-data 서비스 에러 시 graceful degradation")
    void testGetAssetDetailsBySymbolIdentifier_WithPrice_MarketDataError() {
        // given
        String identifier = "KR:KRX:005930";
        when(assetRepository.findByNationalAndMarketAndSymbol("KR", "KRX", "005930"))
                .thenReturn(Mono.just(testAsset));
        when(marketDataServiceClient.getSpotPrice("005930", "KR", "KRX"))
                .thenReturn(Mono.empty()); // 에러 시 empty 반환 (MarketDataServiceClient에서 처리됨)

        // when
        Mono<AssetDetailResponse> result = assetService.getAssetDetailsBySymbolIdentifier(identifier, true);

        // then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertThat(response).isNotNull();
                    assertThat(response.identifier()).isEqualTo("KR:KRX:005930");
                    assertThat(response.symbol()).isEqualTo("005930");
                    assertThat(response.nameKo()).isEqualTo("삼성전자");
                    assertThat(response.price()).isNull(); // 에러 시에도 응답은 성공하지만 price는 null
                })
                .verifyComplete();

        verify(assetRepository, times(1))
                .findByNationalAndMarketAndSymbol("KR", "KRX", "005930");
        verify(marketDataServiceClient, times(1))
                .getSpotPrice("005930", "KR", "KRX");
    }

    @Test
    @DisplayName("존재하지 않는 자산 조회 시 ResourceNotFoundException 발생")
    void testGetAssetDetailsBySymbolIdentifier_AssetNotFound() {
        // given
        String identifier = "KR:KRX:999999";
        when(assetRepository.findByNationalAndMarketAndSymbol("KR", "KRX", "999999"))
                .thenReturn(Mono.empty());

        // when
        Mono<AssetDetailResponse> result = assetService.getAssetDetailsBySymbolIdentifier(identifier, false);

        // then
        StepVerifier.create(result)
                .expectErrorMatches(throwable ->
                        throwable instanceof ResourceNotFoundException &&
                        throwable.getMessage().contains("자산을 찾을 수 없습니다")
                )
                .verify();

        verify(assetRepository, times(1))
                .findByNationalAndMarketAndSymbol("KR", "KRX", "999999");
        verify(marketDataServiceClient, never()).getSpotPrice(anyString(), anyString(), anyString());
    }

    @Test
    @DisplayName("잘못된 식별자 형식 시 IllegalArgumentException 발생")
    void testGetAssetDetailsBySymbolIdentifier_InvalidIdentifierFormat() {
        // given
        String invalidIdentifier = "INVALID_FORMAT";

        // when
        Mono<AssetDetailResponse> result = assetService.getAssetDetailsBySymbolIdentifier(invalidIdentifier, false);

        // then
        StepVerifier.create(result)
                .expectErrorMatches(throwable ->
                        throwable instanceof IllegalArgumentException &&
                        throwable.getMessage().contains("심볼 식별자 형식이 올바르지 않습니다")
                )
                .verify();

        verify(assetRepository, never()).findByNationalAndMarketAndSymbol(anyString(), anyString(), anyString());
        verify(marketDataServiceClient, never()).getSpotPrice(anyString(), anyString(), anyString());
    }

    @Test
    @DisplayName("기본 메서드 호출 시 includePrice=false로 동작")
    void testGetAssetDetailsBySymbolIdentifier_DefaultBehavior() {
        // given
        String identifier = "KR:KRX:005930";
        when(assetRepository.findByNationalAndMarketAndSymbol("KR", "KRX", "005930"))
                .thenReturn(Mono.just(testAsset));

        // when
        Mono<AssetDetailResponse> result = assetService.getAssetDetailsBySymbolIdentifier(identifier);

        // then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertThat(response).isNotNull();
                    assertThat(response.price()).isNull(); // 기본 동작은 가격 정보 없음
                })
                .verifyComplete();

        verify(marketDataServiceClient, never()).getSpotPrice(anyString(), anyString(), anyString());
    }
}
