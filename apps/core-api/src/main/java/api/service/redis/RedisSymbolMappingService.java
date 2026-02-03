package api.service.redis;

import api.redis.RedisKeys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class RedisSymbolMappingService {

    private final ReactiveRedisTemplate<String, String> redisTemplate;

    /**
     * Redis에서 특정 심볼에 매핑된 national:market 조합들을 조회합니다.
     * symbol_map:{symbol} -> SET of "national:market"
     * @param symbol 조회할 심볼
     * @return 해당 심볼에 매핑된 "national:market" 문자열 리스트를 담은 Mono
     */
    public Mono<List<String>> getNationalMarketBySymbol(String symbol) {
        String key = RedisKeys.symbolMap(symbol);
        return redisTemplate.opsForSet().members(key)
                .collectList()
                .doOnSubscribe(s -> log.debug("Redis symbol_map 조회: {}", key))
                .doOnError(e -> log.error("Redis symbol_map 조회 실패 - key: {}, error: {}", key, e.getMessage()));
    }
}
