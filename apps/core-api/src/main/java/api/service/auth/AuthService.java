package api.service.auth;

import api.domain.user.SocialAccount;
import api.domain.user.User;
import api.dto.auth.AuthUserResponse;
import api.exception.AuthException;
import api.repository.user.SocialAccountRepository;
import api.repository.user.UserRepository;
import api.security.jwt.JwtTokenProvider;
import api.security.principal.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Service
@RequiredArgsConstructor
// 토큰 갱신/로그아웃 등 인증 관련 서비스
public class AuthService {

    private final RefreshTokenService refreshTokenService;
    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;
    private final SocialAccountRepository socialAccountRepository;

    public Mono<AuthUserResponse> getCurrentUser(UserPrincipal principal) {
        return userRepository.findByUserIdAndDeletedAtIsNull(principal.getUserId())
            .switchIfEmpty(Mono.error(new AuthException("User not found")))
            .map(user -> AuthUserResponse.from(user, principal.getProvider()));
    }

    public Mono<TokenPair> reIssueTokens(String refreshToken) {
        return refreshTokenService.validateRefreshToken(refreshToken)
            .flatMap(userId -> loadPrincipal(userId)
                .flatMap(principal -> {
                    String accessToken = jwtTokenProvider.createAccessToken(principal);
                    String newRefreshToken = jwtTokenProvider.createRefreshToken();

                    return refreshTokenService.rotateRefreshToken(userId, refreshToken, newRefreshToken)
                        .thenReturn(new TokenPair(accessToken, newRefreshToken));
                }));
    }

    public Mono<Void> logout(UUID userId) {
        return refreshTokenService.deleteRefreshToken(userId);
    }

    private Mono<UserPrincipal> loadPrincipal(UUID userId) {
        Mono<User> userMono = userRepository.findByUserIdAndDeletedAtIsNull(userId)
            .switchIfEmpty(Mono.error(new AuthException("User not found")));

        Mono<SocialAccount> socialMono = socialAccountRepository
            .findAllByUserIdAndIsActiveTrue(userId)
            .next()
            .switchIfEmpty(Mono.error(new AuthException("Social account not found")));

        return Mono.zip(userMono, socialMono)
            .map(tuple -> UserPrincipal.builder()
                .userId(tuple.getT1().getUserId())
                .email(tuple.getT1().getPrimaryEmail())
                .displayName(tuple.getT1().getDisplayName())
                .profileImageUrl(tuple.getT1().getProfileImageUrl())
                .provider(tuple.getT2().getProvider())
                .build());
    }

    public record TokenPair(String accessToken, String refreshToken) {
    }
}
