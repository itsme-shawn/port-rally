package api.exception;

// 토큰 만료 전용 예외
public class TokenExpiredException extends AuthException {

    public TokenExpiredException(String message) {
        super(message);
    }

    public TokenExpiredException(String message, Throwable cause) {
        super(message, cause);
    }
}
