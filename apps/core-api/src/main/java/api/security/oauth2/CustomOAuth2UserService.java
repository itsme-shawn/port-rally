package api.security.oauth2;

import api.domain.user.SocialAccount;
import api.domain.user.User;
import api.enums.user.SocialProvider;
import api.enums.user.UserStatus;
import api.repository.user.SocialAccountRepository;
import api.repository.user.UserRepository;
import api.security.principal.UserPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.client.userinfo.DefaultReactiveOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Mono;

import java.time.Instant;

@Slf4j
@Service
@RequiredArgsConstructor
// OAuth2 로그인 시 사용자 조회/생성 처리
public class CustomOAuth2UserService extends DefaultReactiveOAuth2UserService {

    private final UserRepository userRepository;
    private final SocialAccountRepository socialAccountRepository;
    private final TransactionalOperator transactionalOperator;

    @Override
    public Mono<OAuth2User> loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        return super.loadUser(userRequest)
            .flatMap(oauth2User -> {
                String registrationId = userRequest.getClientRegistration().getRegistrationId();
                OAuth2UserInfo userInfo = OAuth2UserInfo.of(registrationId, oauth2User.getAttributes());

                return processOAuthLogin(userInfo)
                    .map(principal -> (OAuth2User) principal);
            });
    }

    /**
     * OAuth 로그인 처리 로직
     * 1. SocialAccount로 기존 사용자 조회
     * 2. 없으면 신규 User + SocialAccount 생성
     * 3. UserPrincipal 반환
     */
    private Mono<UserPrincipal> processOAuthLogin(OAuth2UserInfo userInfo) {
        SocialProvider provider = userInfo.getProvider();
        String providerUserId = userInfo.getProviderId();

        return socialAccountRepository
            .findByProviderAndProviderUserIdAndRevokedAtIsNullAndIsActiveTrue(provider, providerUserId)
            .flatMap(socialAccount ->
                userRepository.findByUserIdAndDeletedAtIsNull(socialAccount.getUserId())
                    .flatMap(user ->
                        // 기존 사용자: 마지막 로그인 시간 업데이트
                        updateLastLogin(socialAccount)
                            .thenReturn(createUserPrincipal(user, socialAccount, userInfo))
                    )
                    .switchIfEmpty(Mono.defer(() -> {
                        // User가 삭제된 경우: 기존 연동 revoke 후 신규 가입 처리
                        log.info("User deleted, creating new account for {}", userInfo.getEmail());
                        socialAccount.revoke();
                        return socialAccountRepository.save(socialAccount)
                            .then(createNewUser(userInfo));
                    }))
            )
            .switchIfEmpty(
                // 신규 사용자: User + SocialAccount 생성
                createNewUser(userInfo)
            )
            .as(transactionalOperator::transactional);
    }

    private Mono<UserPrincipal> createNewUser(OAuth2UserInfo userInfo) {
        log.info("Creating new user for provider: {}, email: {}",
            userInfo.getProvider(), userInfo.getEmail());

        // 신규 사용자는 PENDING 상태로 생성 (약관 동의 후 ACTIVE로 전환)
        User newUser = User.builder()
            .displayName(userInfo.getName())
            .primaryEmail(userInfo.getEmail())
            .primaryEmailVerified(userInfo.isEmailVerified())
            .profileImageUrl(userInfo.getImageUrl())
            .status(UserStatus.PENDING)  // ACTIVE → PENDING 변경
            // signupCompletedAt은 약관 동의 후 설정
            .build();

        return userRepository.save(newUser)
            .flatMap(savedUser -> {
                SocialAccount socialAccount = SocialAccount.builder()
                    .userId(savedUser.getUserId())
                    .provider(userInfo.getProvider())
                    .providerUserId(userInfo.getProviderId())
                    .providerEmail(userInfo.getEmail())
                    .providerEmailVerified(userInfo.isEmailVerified())
                    .linkedAt(Instant.now())
                    .lastLoginAt(Instant.now())
                    .isActive(true)
                    .build();

                return socialAccountRepository.save(socialAccount)
                    .map(sa -> createUserPrincipal(savedUser, sa, userInfo));
            });
    }

    private Mono<Void> updateLastLogin(SocialAccount socialAccount) {
        socialAccount.updateLastLogin();
        return socialAccountRepository.save(socialAccount).then();
    }

    private UserPrincipal createUserPrincipal(User user, SocialAccount socialAccount,
            OAuth2UserInfo userInfo) {
        return UserPrincipal.builder()
            .userId(user.getUserId())
            .email(user.getPrimaryEmail())
            .displayName(user.getDisplayName())
            .profileImageUrl(user.getProfileImageUrl())
            .provider(socialAccount.getProvider())
            .attributes(userInfo.getAttributes())
            .build();
    }
}
