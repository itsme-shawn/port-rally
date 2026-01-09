package api.security.handler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.server.authorization.HttpStatusServerAccessDeniedHandler;
import org.springframework.security.web.server.authorization.ServerAccessDeniedHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.security.Principal;

@Slf4j
@Component
// 403 응답 시 요청 정보를 로그로 남김
public class LoggingServerAccessDeniedHandler implements ServerAccessDeniedHandler {

    // 인가 실패(403) 로그를 남기기 위한 핸들러
    private final ServerAccessDeniedHandler delegate =
        new HttpStatusServerAccessDeniedHandler(HttpStatus.FORBIDDEN);

    @Override
    public Mono<Void> handle(ServerWebExchange exchange, AccessDeniedException denied) {
        Mono<Void> logMono = exchange.getPrincipal()
            .cast(Principal.class)
            .doOnNext(principal -> log.warn("Access denied: method={} path={} principal={} message={}",
                exchange.getRequest().getMethod(),
                exchange.getRequest().getPath().value(),
                principal.getName(),
                denied.getMessage()))
            .switchIfEmpty(Mono.fromRunnable(() -> log.warn(
                "Access denied: method={} path={} principal=anonymous message={}",
                exchange.getRequest().getMethod(),
                exchange.getRequest().getPath().value(),
                denied.getMessage())))
            .then();

        return logMono.then(delegate.handle(exchange, denied));
    }
}
