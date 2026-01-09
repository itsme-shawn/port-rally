package api.security.handler;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.server.WebFilterExchange;
import org.springframework.security.web.server.authentication.ServerAuthenticationFailureHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

import java.net.URI;

@Slf4j
@Component
// OAuth2 실패 시 에러 파라미터를 포함해 리다이렉트
public class OAuth2AuthenticationFailureHandler implements ServerAuthenticationFailureHandler {

    @Value("${oauth2.failure-redirect-uri}")
    private String failureRedirectUri;

    @Override
    public Mono<Void> onAuthenticationFailure(WebFilterExchange webFilterExchange,
            AuthenticationException exception) {

        String errorMessage = exception.getMessage();
        log.error("OAuth2 authentication failed: {}", errorMessage);

        return Mono.fromRunnable(() -> {
            var response = webFilterExchange.getExchange().getResponse();

            // authorization_request_not_found 에러면 OAuth2 로그인 다시 시작
            // (뒤로가기 후 재시도, 세션 만료 등의 경우)
            if (errorMessage != null && errorMessage.contains("authorization_request_not_found")) {
                log.info("Redirecting to OAuth2 authorization due to stale request");
                response.setStatusCode(HttpStatus.FOUND);
                response.getHeaders().setLocation(URI.create("/oauth2/authorization/google"));
                return;
            }

            String redirectUrl = UriComponentsBuilder
                .fromUriString(failureRedirectUri)
                .queryParam("error", errorMessage)
                .build()
                .encode()
                .toUriString();

            response.setStatusCode(HttpStatus.FOUND);
            response.getHeaders().setLocation(URI.create(redirectUrl));
        });
    }
}
