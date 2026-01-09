package api.service.user;

import api.exception.AuthException;
import api.repository.user.SocialAccountRepository;
import api.repository.user.UserRepository;
import api.service.auth.RefreshTokenService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class WithdrawalService {

    private final UserRepository userRepository;
    private final SocialAccountRepository socialAccountRepository;
    private final RefreshTokenService refreshTokenService;
    private final TransactionalOperator transactionalOperator;

    public Mono<Void> withdrawUser(UUID userId) {
        // 탈퇴 처리: 사용자 soft delete -> 소셜 계정 revoke -> refresh token 삭제
        return userRepository.findByUserIdAndDeletedAtIsNull(userId)
            .switchIfEmpty(Mono.error(new AuthException("User not found or already deleted")))
            .flatMap(user -> {
                user.softDelete();
                return userRepository.save(user);
            })
            .flatMap(savedUser -> socialAccountRepository.findAllByUserIdAndIsActiveTrue(savedUser.getUserId())
                .flatMap(socialAccount -> {
                    socialAccount.revoke();
                    return socialAccountRepository.save(socialAccount);
                })
                .then(refreshTokenService.deleteRefreshToken(savedUser.getUserId()))
            )
            .doOnSuccess(unused -> log.info("User withdrawn: {}", userId))
            .as(transactionalOperator::transactional);
    }
}
