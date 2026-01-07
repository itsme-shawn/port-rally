package api.service.terms;

import api.domain.terms.Terms;
import api.domain.terms.UserTermsAgreement;
import api.dto.terms.TermsResponse;
import api.repository.terms.TermsRepository;
import api.repository.terms.UserTermsAgreementRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class TermsService {

    private final TermsRepository termsRepository;
    private final UserTermsAgreementRepository agreementRepository;

    /**
     * 현재 유효한 약관 목록 조회 (display_order 순서)
     */
    public Flux<TermsResponse> getActiveTerms() {
        return termsRepository.findAllByIsActiveTrueOrderByDisplayOrderAsc()
            .map(TermsResponse::from);
    }

    /**
     * 필수 약관 목록 조회
     */
    public Flux<Terms> getRequiredTerms() {
        return termsRepository.findAllByIsActiveTrueAndIsRequiredTrue();
    }

    /**
     * 사용자의 약관 동의 이력 조회
     */
    public Flux<UserTermsAgreement> getUserAgreements(UUID userId) {
        return agreementRepository.findAllByUserId(userId);
    }

    /**
     * 약관 동의 정보 저장
     */
    public Mono<UserTermsAgreement> saveAgreement(UUID userId, UUID termsId,
            Boolean agreed, String ipAddress, String userAgent) {
        UserTermsAgreement agreement = UserTermsAgreement.builder()
            .userId(userId)
            .termsId(termsId)
            .agreed(agreed)
            .agreedAt(Instant.now())
            .ipAddress(ipAddress)
            .userAgent(userAgent)
            .build();

        return agreementRepository.save(agreement);
    }

    /**
     * 필수 약관 모두 동의했는지 검증
     */
    public Mono<Boolean> validateRequiredTermsAgreed(List<UUID> agreedTermsIds) {
        return getRequiredTerms()
            .map(Terms::getTermsId)
            .collectList()
            .map(requiredIds -> requiredIds.stream()
                .allMatch(agreedTermsIds::contains));
    }
}
