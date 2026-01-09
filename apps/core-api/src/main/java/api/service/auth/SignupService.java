package api.service.auth;

import api.dto.auth.SignupCompleteRequest;
import api.dto.auth.SignupCompleteResponse;
import api.enums.user.UserStatus;
import api.exception.AuthException;
import api.repository.user.UserRepository;
import api.service.terms.TermsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class SignupService {

    private final UserRepository userRepository;
    private final TermsService termsService;
    private final TransactionalOperator transactionalOperator;

    /**
     * 회원가입 완료 처리
     * 1. 필수 약관 동의 여부 검증
     * 2. 약관 동의 정보 저장
     * 3. User 상태를 PENDING → ACTIVE로 변경
     * 4. signupCompletedAt, termsAcceptedAt 설정
     */
    public Mono<SignupCompleteResponse> completeSignup(
            UUID userId,
            SignupCompleteRequest request,
            String ipAddress,
            String userAgent) {

        // 동의한 약관 ID 목록 추출
        var agreedTermsIds = request.getAgreements().stream()
            .filter(SignupCompleteRequest.TermsAgreementItem::getAgreed)
            .map(SignupCompleteRequest.TermsAgreementItem::getTermsId)
            .collect(Collectors.toList());

        return termsService.validateRequiredTermsAgreed(agreedTermsIds)
            .flatMap(isValid -> {
                if (!isValid) {
                    return Mono.error(new AuthException("필수 약관에 모두 동의해야 합니다"));
                }

                // 사용자 조회
                return userRepository.findByUserIdAndDeletedAtIsNull(userId)
                    .switchIfEmpty(Mono.error(new AuthException("사용자를 찾을 수 없습니다")))
                    .flatMap(user -> {
                        // PENDING 상태 확인
                        if (user.getStatus() != UserStatus.PENDING) {
                            return Mono.error(new AuthException(
                                "이미 회원가입이 완료된 사용자입니다"));
                        }

                        // 약관 동의 정보 저장
                        return Flux.fromIterable(request.getAgreements())
                            .flatMap(agreement -> termsService.saveAgreement(
                                userId,
                                agreement.getTermsId(),
                                agreement.getAgreed(),
                                ipAddress,
                                userAgent
                            ))
                            .then(Mono.just(user));
                    })
                    .flatMap(user -> {
                        // User 상태 업데이트
                        user.setStatus(UserStatus.ACTIVE);
                        user.setSignupCompletedAt(Instant.now());
                        user.setTermsAcceptedAt(Instant.now());

                        return userRepository.save(user);
                    })
                    .map(user -> {
                        log.info("Signup completed for user: {}", user.getUserId());
                        return SignupCompleteResponse.success(user.getUserId());
                    });
            })
            .as(transactionalOperator::transactional);
    }
}
