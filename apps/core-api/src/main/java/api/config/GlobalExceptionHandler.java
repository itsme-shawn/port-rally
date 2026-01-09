package api.config;

import api.exception.AuthException;
import api.exception.TokenExpiredException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.r2dbc.BadSqlGrammarException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.support.WebExchangeBindException;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 전역 예외 핸들러
 * - 모든 예외의 root cause를 로깅
 * - 클라이언트에게 적절한 에러 응답 반환
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BadSqlGrammarException.class)
    public Mono<ResponseEntity<Map<String, Object>>> handleBadSqlGrammarException(BadSqlGrammarException e) {
        Throwable rootCause = getRootCause(e);

        log.error("=== SQL Grammar Error ===");
        log.error("Message: {}", e.getMessage());
        log.error("SQL: {}", e.getSql());
        log.error("Root cause: {} - {}", rootCause.getClass().getName(), rootCause.getMessage());
        log.error("Stack trace:\n{}", getFilteredStackTrace(e));

        Map<String, Object> body = createErrorBody(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "Database error: " + rootCause.getMessage()
        );

        return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body));
    }

    @ExceptionHandler(WebExchangeBindException.class)
    public Mono<ResponseEntity<Map<String, Object>>> handleValidationException(WebExchangeBindException e) {
        log.warn("Validation failed: {}", e.getMessage());

        Map<String, Object> body = createErrorBody(HttpStatus.BAD_REQUEST, "Validation failed");
        body.put("errors", e.getFieldErrors().stream()
            .map(err -> Map.of(
                "field", err.getField(),
                "message", err.getDefaultMessage() != null ? err.getDefaultMessage() : "Invalid value",
                "rejectedValue", err.getRejectedValue() != null ? err.getRejectedValue().toString() : "null"
            ))
            .toList());

        return Mono.just(ResponseEntity.badRequest().body(body));
    }

    @ExceptionHandler(TokenExpiredException.class)
    public Mono<ResponseEntity<Map<String, Object>>> handleTokenExpiredException(TokenExpiredException e) {
        log.warn("Token expired: {}", e.getMessage());

        Map<String, Object> body = createErrorBody(HttpStatus.UNAUTHORIZED, e.getMessage());
        return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(body));
    }

    @ExceptionHandler(AuthException.class)
    public Mono<ResponseEntity<Map<String, Object>>> handleAuthException(AuthException e) {
        log.warn("Authentication error: {}", e.getMessage());

        Map<String, Object> body = createErrorBody(HttpStatus.UNAUTHORIZED, e.getMessage());
        return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(body));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public Mono<ResponseEntity<Map<String, Object>>> handleIllegalArgumentException(IllegalArgumentException e) {
        log.warn("Illegal argument: {}", e.getMessage());

        Map<String, Object> body = createErrorBody(HttpStatus.BAD_REQUEST, e.getMessage());
        return Mono.just(ResponseEntity.badRequest().body(body));
    }

    @ExceptionHandler(Exception.class)
    public Mono<ResponseEntity<Map<String, Object>>> handleGenericException(Exception e) {
        Throwable rootCause = getRootCause(e);

        log.error("=== Unhandled Exception ===");
        log.error("Exception: {} - {}", e.getClass().getName(), e.getMessage());
        log.error("Root cause: {} - {}", rootCause.getClass().getName(), rootCause.getMessage());
        log.error("Stack trace:\n{}", getFilteredStackTrace(e));

        Map<String, Object> body = createErrorBody(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "Internal server error"
        );
        // TODO 개발 환경에서만 상세 정보 포함하도록 추가
        body.put("rootCause", rootCause.getMessage());
        body.put("rootCauseClass", rootCause.getClass().getSimpleName());

        return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body));
    }

    private Throwable getRootCause(Throwable e) {
        Throwable rootCause = e;
        while (rootCause.getCause() != null && rootCause.getCause() != rootCause) {
            rootCause = rootCause.getCause();
        }
        return rootCause;
    }

    /**
     * 스택 트레이스에서 핵심 정보만 필터링
     * - api.* 패키지 (프로젝트 코드)
     * - 원인 체인의 첫 번째 프레임들
     */
    private String getFilteredStackTrace(Throwable e) {
        StringBuilder sb = new StringBuilder();
        Throwable current = e;
        int depth = 0;

        while (current != null && depth <10) {
            if (depth > 0) {
                sb.append("Caused by: ");
            }
            sb.append(current.getClass().getName())
              .append(": ")
              .append(current.getMessage())
              .append("\n");

            for (StackTraceElement frame : current.getStackTrace()) {
                String className = frame.getClassName();
                // 프로젝트 코드 또는 Spring의 핵심 진입점만 표시
                if (className.startsWith("api.") ||
                    className.contains("Controller") ||
                    className.contains("Service") ||
                    className.contains("Repository")) {
                    sb.append("    at ").append(frame).append("\n");
                }
            }

            current = current.getCause();
            depth++;
        }

        return sb.toString();
    }

    private Map<String, Object> createErrorBody(HttpStatus status, String message) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("timestamp", Instant.now().toString());
        body.put("status", status.value());
        body.put("error", status.getReasonPhrase());
        body.put("message", message);
        return body;
    }
}
