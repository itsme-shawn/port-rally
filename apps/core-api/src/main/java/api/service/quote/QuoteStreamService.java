package api.service.quote;

import api.dto.quote.QuoteStreamDto;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.ReactiveRedisConnectionFactory;
import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

import java.time.Duration;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 실시간 시세 스트리밍 서비스.
 * Redis Pub/Sub "quotes" 채널을 구독하여 실시간 시세를 전달합니다.
 */
@Slf4j
@Service
public class QuoteStreamService {

    private final ReactiveRedisConnectionFactory redisConnectionFactory;
    private final ObjectMapper objectMapper;

    private static final String QUOTES_CHANNEL = "quotes";

    public QuoteStreamService(ReactiveRedisConnectionFactory redisConnectionFactory, ObjectMapper objectMapper) {
        this.redisConnectionFactory = redisConnectionFactory;
        this.objectMapper = objectMapper;
    }

    /**
     * 지정된 심볼들의 실시간 시세를 스트리밍합니다.
     *
     * @param symbols 구독할 심볼 목록
     * @return 실시간 시세 Flux
     */
    public Flux<QuoteStreamDto> subscribe(List<String> symbols) {
        if (symbols == null || symbols.isEmpty()) {
            log.warn("No symbols provided for quote streaming");
            return Flux.empty();
        }

        Set<String> symbolSet = symbols.stream()
                .map(String::toUpperCase)
                .collect(Collectors.toSet());

        log.info("Starting quote stream for symbols: {}", symbolSet);

        return createQuoteFlux()
                .filter(quote -> quote != null && symbolSet.contains(quote.getSymbol()))
                .doOnNext(quote -> log.debug("Streaming quote: {} = {}", quote.getSymbol(), quote.getPrice()))
                .doOnSubscribe(sub -> log.info("Client subscribed to quote stream for symbols: {}", symbolSet))
                .doOnCancel(() -> log.info("Quote stream cancelled for symbols: {}", symbolSet));
    }

    /**
     * 모든 심볼의 실시간 시세를 스트리밍합니다.
     *
     * @return 실시간 시세 Flux
     */
    public Flux<QuoteStreamDto> subscribeAll() {
        log.info("Starting quote stream for all symbols");

        return createQuoteFlux()
                .filter(quote -> quote != null)
                .doOnNext(quote -> log.debug("Streaming quote: {} = {}", quote.getSymbol(), quote.getPrice()))
                .doOnSubscribe(sub -> log.info("Client subscribed to quote stream for all symbols"))
                .doOnCancel(() -> log.info("Quote stream cancelled for all symbols"));
    }

    /**
     * Redis Pub/Sub 구독 및 메시지 스트림 생성.
     */
    private Flux<QuoteStreamDto> createQuoteFlux() {
        // ReactiveRedisMessageListenerContainer 생성
        ReactiveRedisMessageListenerContainer container =
                new ReactiveRedisMessageListenerContainer(redisConnectionFactory);

        // "quotes" 채널 구독
        return container.receive(ChannelTopic.of(QUOTES_CHANNEL))
                .map(message -> message.getMessage())
                .map(this::parseQuote)
                .onErrorResume(e -> {
                    log.error("Error in quote stream: {}", e.getMessage());
                    return Flux.empty();
                })
                .timeout(Duration.ofMinutes(30), Flux.empty()) // 30분 타임아웃
                .doOnSubscribe(sub -> {
                    log.info("Subscribed to Redis Pub/Sub channel: {}", QUOTES_CHANNEL);
                    container.destroyLater(); // cleanup on completion
                })
                .doFinally(signal -> {
                    log.info("Cleaning up Redis subscription, signal: {}", signal);
                    container.destroyLater();
                });
    }

    /**
     * Redis 메시지를 QuoteStreamDto로 파싱.
     *
     * @param message Redis에서 수신한 메시지 (JSON 문자열)
     * @return 파싱된 QuoteStreamDto, 실패 시 null
     */
    private QuoteStreamDto parseQuote(String message) {
        try {
            QuoteStreamDto quote = objectMapper.readValue(message, QuoteStreamDto.class);

            // 필수 필드 검증
            if (quote.getSymbol() == null || quote.getPrice() == null) {
                log.warn("Invalid quote message (missing required fields): {}", message);
                return null;
            }

            return quote;
        } catch (Exception e) {
            log.warn("Failed to parse quote message: {} - Error: {}", message, e.getMessage());
            return null;
        }
    }
}
