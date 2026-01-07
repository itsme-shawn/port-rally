package api.security.handler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.server.ServerAuthenticationEntryPoint;
import org.springframework.security.web.server.authentication.HttpStatusServerEntryPoint;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Slf4j
@Component
// 401 응답 시 요청 정보를 로그로 남김
public class LoggingServerAuthenticationEntryPoint implements ServerAuthenticationEntryPoint {

    // 인증 실패(401) 로그를 남기기 위한 엔트리 포인트
    private final ServerAuthenticationEntryPoint delegate =
        new HttpStatusServerEntryPoint(HttpStatus.UNAUTHORIZED);

    @Override
    public Mono<Void> commence(ServerWebExchange exchange, AuthenticationException ex) {
        log.warn("Unauthorized request: method={} path={} message={}",
            exchange.getRequest().getMethod(),
            exchange.getRequest().getPath().value(),
            ex.getMessage());
        return delegate.commence(exchange, ex);
    }
}
