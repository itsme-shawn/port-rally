package api.controller;

import api.dto.quote.QuoteStreamDto;
import api.service.asset.MarketDataServiceClient;
import api.service.quote.QuoteStreamService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.util.UriUtils;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;

/**
 * 실시간 시세 스트리밍 API.
 * Server-Sent Events (SSE)를 사용하여 실시간 시세를 클라이언트에 전달합니다.
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/quotes")
@RequiredArgsConstructor
@Tag(name = "Quote", description = "실시간 시세 API")
public class QuoteController {

    private static final String DEFAULT_PROVIDER = "kis";

    private final QuoteStreamService quoteStreamService;
    private final MarketDataServiceClient marketDataServiceClient;

    /**
     * 지정된 심볼들의 실시간 시세를 스트리밍합니다.
     *
     * @param symbols 구독할 심볼 목록 (쉼표로 구분)
     * @return SSE 스트림
     */
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(
            summary = "실시간 시세 스트리밍",
            description = "SSE를 통해 지정된 심볼들의 실시간 시세를 수신합니다. " +
                    "연결을 유지하며 시세가 업데이트될 때마다 이벤트를 받습니다."
    )
    public Flux<ServerSentEvent<QuoteStreamDto>> streamQuotes(
            @Parameter(description = "구독할 심볼 목록 (예: 005930,035720)", required = true)
            @RequestParam List<String> symbols
    ) {
        log.info("SSE connection opened for symbols: {}", symbols);

        Mono<Void> registration = marketDataServiceClient.registerActiveSymbols(DEFAULT_PROVIDER, symbols)
                .onErrorResume(e -> {
                    log.warn("Failed to register active_symbols:{} - {}", DEFAULT_PROVIDER, e.getMessage());
                    return Mono.empty();
                });

        return registration.thenMany(quoteStreamService.subscribe(symbols))
                .map(quote -> ServerSentEvent.<QuoteStreamDto>builder()
                        .event("quote-update")
                        .id(quote.getSymbol() + "-" + System.currentTimeMillis())
                        .data(quote)
                        .build()
                )
                // Heartbeat: 30초마다 comment 전송 (연결 유지)
                .mergeWith(
                        Flux.interval(Duration.ofSeconds(30))
                                .map(seq -> ServerSentEvent.<QuoteStreamDto>builder()
                                        .comment("heartbeat")
                                        .build()
                                )
                )
                .doOnCancel(() -> log.info("SSE connection cancelled for symbols: {}", symbols))
                .doOnComplete(() -> log.info("SSE connection completed for symbols: {}", symbols))
                .doOnError(e -> log.error("SSE connection error for symbols: {} - {}", symbols, e.getMessage()));
    }

    /**
     * 단일 종목 식별자로 실시간 시세를 스트리밍합니다.
     *
     * @param identifier 종목 식별자 (예: KR:KOSPI:005930)
     * @return SSE 스트림
     */
    @GetMapping(value = "/stream/{identifier}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(
            summary = "단일 종목 실시간 스트리밍",
            description = "종목 식별자(national:exchange:symbol)로 실시간 시세를 수신합니다."
    )
    public Flux<ServerSentEvent<QuoteStreamDto>> streamQuoteByIdentifier(
            @Parameter(description = "종목 식별자 (예: KR:KOSPI:005930)", required = true)
            @PathVariable String identifier
    ) {
        String normalizedIdentifier = normalizeIdentifier(identifier);
        // KR:KOSPI:005930 → symbol 추출
        String[] parts = normalizedIdentifier.split(":");
        if (parts.length < 3) {
            log.warn("Invalid identifier format: {} (normalized: {})", identifier, normalizedIdentifier);
            return Flux.empty();
        }
        String symbol = parts[2];

        log.info("SSE connection opened for identifier: {} (symbol: {})", normalizedIdentifier, symbol);

        return streamQuotes(List.of(symbol));
    }

    /**
     * 모든 심볼의 실시간 시세를 스트리밍합니다.
     * 주의: 대량의 데이터가 전송될 수 있습니다.
     *
     * @return SSE 스트림
     */
    @GetMapping(value = "/stream/all", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(
            summary = "전체 종목 실시간 스트리밍",
            description = "⚠️ 주의: 모든 종목의 실시간 시세를 수신합니다. 대량의 데이터가 전송될 수 있습니다."
    )
    public Flux<ServerSentEvent<QuoteStreamDto>> streamAllQuotes() {
        log.info("SSE connection opened for all symbols");

        return quoteStreamService.subscribeAll()
                .map(quote -> ServerSentEvent.<QuoteStreamDto>builder()
                        .event("quote-update")
                        .id(quote.getSymbol() + "-" + System.currentTimeMillis())
                        .data(quote)
                        .build()
                )
                .mergeWith(
                        Flux.interval(Duration.ofSeconds(30))
                                .map(seq -> ServerSentEvent.<QuoteStreamDto>builder()
                                        .comment("heartbeat")
                                        .build()
                                )
                )
                .doOnCancel(() -> log.info("SSE connection cancelled for all symbols"))
                .doOnComplete(() -> log.info("SSE connection completed for all symbols"))
                .doOnError(e -> log.error("SSE connection error for all symbols: {}", e.getMessage()));
    }

    private String normalizeIdentifier(String identifier) {
        if (identifier == null || !identifier.contains("%")) {
            return identifier;
        }
        try {
            return UriUtils.decode(identifier, StandardCharsets.UTF_8);
        } catch (IllegalArgumentException e) {
            log.warn("Failed to decode identifier: {} - {}", identifier, e.getMessage());
            return identifier;
        }
    }
}
