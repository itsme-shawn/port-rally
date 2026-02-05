package api.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Slf4j
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
// 모든 응답 상태를 기록하는 전역 WebFilter
public class ResponseStatusLoggingWebFilter implements WebFilter {

    // 모든 응답을 기록하되, 4xx/5xx는 WARN으로 분리해 문제 추적을 돕는다.
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        return chain.filter(exchange)
            .doFinally(signalType -> {
                HttpStatusCode statusCode = exchange.getResponse().getStatusCode();
                if (statusCode == null) {
                    log.info("HTTP response: status=unknown method={} path={}",
                        exchange.getRequest().getMethod(),
                        exchange.getRequest().getPath().value());
                    return;
                }

                int rawStatus = statusCode.value();
                HttpStatus status = HttpStatus.resolve(rawStatus);
                String statusText = status != null ? status.toString() : String.valueOf(rawStatus);

                if (rawStatus >= 400) {
                    log.warn("HTTP response: status={} method={} path={}",
                        statusText,
                        exchange.getRequest().getMethod(),
                        exchange.getRequest().getPath().value());
                } else {
                    log.info("HTTP response: status={} method={} path={}",
                        statusText,
                        exchange.getRequest().getMethod(),
                        exchange.getRequest().getPath().value());
                }
            });
    }
}
