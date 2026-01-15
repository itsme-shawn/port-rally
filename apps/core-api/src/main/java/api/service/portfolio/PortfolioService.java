package api.service.portfolio;

import api.domain.portfolio.Portfolio;
import api.domain.portfolio.Position;
import api.dto.portfolio.CreatePortfolioRequest;
import api.dto.portfolio.PortfolioResponse;
import api.dto.portfolio.UpdatePortfolioRequest;
import api.enums.portfolio.SourceType;
import api.exception.ResourceNotFoundException;
import api.repository.ocr.UploadedImageRepository;
import api.repository.portfolio.PortfolioRepository;
import api.repository.portfolio.PositionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class PortfolioService {

    private final PortfolioRepository portfolioRepository;
    private final PositionRepository positionRepository;
    private final UploadedImageRepository uploadedImageRepository;

    /**
     * 사용자의 포트폴리오 존재 여부 확인
     *
     * @param userId 사용자 ID
     * @return 포트폴리오 존재 여부 (true: 존재, false: 미존재)
     */
    public Mono<Boolean> hasPortfolio(UUID userId) {
        return portfolioRepository.countByUserIdAndDeletedAtIsNull(userId)
            .map(count -> count > 0)
            .doOnNext(hasPortfolio ->
                log.debug("User {} portfolio check: {}", userId, hasPortfolio));
    }

    /**
     * 포트폴리오 생성
     */
    @Transactional
    public Mono<PortfolioResponse> createPortfolio(UUID userId, CreatePortfolioRequest request) {
        return portfolioRepository.countByUserIdAndDeletedAtIsNull(userId)
            .flatMap(count -> {
                boolean isFirstPortfolio = count == 0;
                boolean isPrimary = isFirstPortfolio || Boolean.TRUE.equals(request.isPrimary());

                Mono<Void> resetPrimaryMono = isPrimary
                    ? portfolioRepository.resetPrimaryFlags(userId).then()
                    : Mono.empty();

                Portfolio newPortfolio = Portfolio.builder()
                    .userId(userId)
                    .portfolioName(request.name())
                    .description(request.description())
                    .investmentType(request.investmentType())
                    .isPrimary(isPrimary)
                    .baseCurrency("KRW") // 기본값
                    .build();

                return resetPrimaryMono
                    .then(portfolioRepository.save(newPortfolio));
            })
            .flatMap(savedPortfolio -> {
                Mono<Void> savePositionsMono = Mono.empty();
                if (request.initialPositions() != null && !request.initialPositions().isEmpty()) {
                    var positions = request.initialPositions().stream()
                        .map(posReq -> {
                            BigDecimal costBasis = posReq.averageCost().multiply(posReq.quantity());
                            return Position.builder()
                                .portfolioId(savedPortfolio.getPortfolioId())
                                .assetId(posReq.assetId())
                                .quantity(posReq.quantity())
                                .averageCost(posReq.averageCost())
                                .costBasis(costBasis)
                                .value(costBasis) // 기존 value 필드는 costBasis로 초기화
                                .positionValue(posReq.positionValue()) // 신설 필드 매핑
                                .sourceType(SourceType.MANUAL)
                                .currency(posReq.currency())
                                .purchaseDate(posReq.purchaseDate())
                                .broker(posReq.broker())
                                .accountAlias(posReq.accountAlias())
                                .build();
                        })
                        .collect(Collectors.toList());
                    savePositionsMono = positionRepository.saveAll(positions).then();
                }

                return savePositionsMono
                    .thenReturn(savedPortfolio);
            })
            .map(PortfolioResponse::from);
    }

    /**
     * 내 포트폴리오 목록 조회
     */
    public Flux<PortfolioResponse> getPortfolios(UUID userId) {
        return portfolioRepository.findAllByUserIdAndDeletedAtIsNull(userId)
            .map(PortfolioResponse::from);
    }

    /**
     * 포트폴리오 단건 조회
     */
    public Mono<PortfolioResponse> getPortfolio(UUID userId, UUID portfolioId) {
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
            .filter(portfolio -> portfolio.getUserId().equals(userId))
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
            .map(PortfolioResponse::from);
    }

    /**
     * 포트폴리오 수정
     */
    @Transactional
    public Mono<PortfolioResponse> updatePortfolio(UUID userId, UUID portfolioId, UpdatePortfolioRequest request) {
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
            .filter(portfolio -> portfolio.getUserId().equals(userId))
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
            .flatMap(portfolio -> {
                boolean primaryChanged = request.isPrimary() != null && request.isPrimary() && !portfolio.getIsPrimary();

                if (request.name() != null) portfolio.setPortfolioName(request.name());
                if (request.description() != null) portfolio.setDescription(request.description());
                if (request.goal() != null) portfolio.setGoal(request.goal());
                if (request.investmentType() != null) portfolio.setInvestmentType(request.investmentType());
                if (request.isPrimary() != null) portfolio.setIsPrimary(request.isPrimary());

                Mono<Void> resetPrimaryMono = primaryChanged
                    ? portfolioRepository.resetPrimaryFlags(userId).then()
                    : Mono.empty();

                return resetPrimaryMono.then(portfolioRepository.save(portfolio));
            })
            .map(PortfolioResponse::from);
    }

    /**
     * 포트폴리오 삭제 (Soft Delete)
     */
    @Transactional
    public Mono<Void> deletePortfolio(UUID userId, UUID portfolioId) {
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
            .filter(portfolio -> portfolio.getUserId().equals(userId))
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
            .flatMap(portfolio -> {
                portfolio.softDelete();
                return portfolioRepository.save(portfolio);
            })
            .then();
    }
}
