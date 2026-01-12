package api.service.portfolio;

import api.domain.portfolio.Position;
import api.dto.portfolio.AddPositionRequest;
import api.dto.portfolio.PositionResponse;
import api.enums.portfolio.SourceType;
import api.exception.ResourceNotFoundException;
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

@Slf4j
@Service
@RequiredArgsConstructor
public class PositionService {

    private final PositionRepository positionRepository;
    private final PortfolioRepository portfolioRepository;

    /**
     * 포지션 추가 (수기 입력)
     */
    @Transactional
    public Mono<PositionResponse> addPosition(UUID userId, UUID portfolioId, AddPositionRequest request) {
        // 1. 포트폴리오 존재 및 소유권 확인
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
            .filter(portfolio -> portfolio.getUserId().equals(userId))
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
            .flatMap(portfolio -> 
                // 2. 중복 포지션 체크
                positionRepository.existsByPortfolioIdAndAssetIdAndDeletedAtIsNull(portfolioId, request.assetId())
                    .flatMap(exists -> {
                        if (exists) {
                            return Mono.error(new IllegalArgumentException("이미 해당 자산의 포지션이 존재합니다. 수정 기능을 이용해주세요."));
                        }
                        
                        // 3. Position 엔티티 생성
                        BigDecimal costBasis = request.averageCost().multiply(request.quantity());
                        // 현재가는 임시로 평단가와 동일하게 설정 (추후 시세 연동 시 변경)
                        BigDecimal initialValue = costBasis;

                        Position position = Position.builder()
                            .portfolioId(portfolioId)
                            .assetId(request.assetId())
                            .quantity(request.quantity())
                            .averageCost(request.averageCost())
                            .costBasis(costBasis)
                            .value(initialValue)
                            .sourceType(SourceType.MANUAL)
                            .currency(request.currency())
                            .purchaseDate(request.purchaseDate())
                            .broker(request.broker())
                            .accountAlias(request.accountAlias())
                            .build();

                        // 4. 저장 및 응답 변환
                        return positionRepository.save(position)
                            .map(PositionResponse::from);
                    })
            );
    }

    /**
     * 포트폴리오의 포지션 목록 조회
     */
    public Flux<PositionResponse> getPositions(UUID userId, UUID portfolioId) {
        return portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(portfolioId)
            .filter(portfolio -> portfolio.getUserId().equals(userId))
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포트폴리오를 찾을 수 없거나 접근 권한이 없습니다.")))
            .flatMapMany(portfolio -> positionRepository.findAllByPortfolioIdAndDeletedAtIsNull(portfolioId))
            .map(PositionResponse::from);
    }

    /**
     * 포지션 수정
     */
    @Transactional
    public Mono<PositionResponse> updatePosition(UUID userId, UUID positionId, api.dto.portfolio.UpdatePositionRequest request) {
        return positionRepository.findByPositionIdAndDeletedAtIsNull(positionId)
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포지션을 찾을 수 없습니다.")))
            .flatMap(position ->
                portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(position.getPortfolioId())
                    .filter(portfolio -> portfolio.getUserId().equals(userId))
                    .switchIfEmpty(Mono.error(new ResourceNotFoundException("접근 권한이 없습니다.")))
                    .map(portfolio -> position)
            )
            .flatMap(position -> {
                if (request.assetId() != null) position.setAssetId(request.assetId());
                if (request.quantity() != null) position.setQuantity(request.quantity());
                if (request.averageCost() != null) position.setAverageCost(request.averageCost());
                if (request.currency() != null) position.setCurrency(request.currency());
                if (request.purchaseDate() != null) position.setPurchaseDate(request.purchaseDate());
                if (request.broker() != null) position.setBroker(request.broker());
                if (request.accountAlias() != null) position.setAccountAlias(request.accountAlias());

                // 재계산 (수량 or 평단가 변경 시)
                if (request.quantity() != null || request.averageCost() != null) {
                    BigDecimal qty = position.getQuantity();
                    BigDecimal avg = position.getAverageCost();
                    BigDecimal newCostBasis = qty.multiply(avg);
                    position.setCostBasis(newCostBasis);
                    // 현재가는 시세 연동 전까지 평단가 기준으로 갱신
                    position.setValue(newCostBasis);
                }

                return positionRepository.save(position);
            })
            .map(PositionResponse::from);
    }

    /**
     * 포지션 삭제 (Soft Delete)
     */
    @Transactional
    public Mono<Void> deletePosition(UUID userId, UUID positionId) {
        return positionRepository.findByPositionIdAndDeletedAtIsNull(positionId)
            .switchIfEmpty(Mono.error(new ResourceNotFoundException("포지션을 찾을 수 없습니다.")))
            .flatMap(position ->
                portfolioRepository.findByPortfolioIdAndDeletedAtIsNull(position.getPortfolioId())
                    .filter(portfolio -> portfolio.getUserId().equals(userId))
                    .switchIfEmpty(Mono.error(new ResourceNotFoundException("접근 권한이 없습니다.")))
                    .map(portfolio -> position)
            )
            .flatMap(position -> {
                position.softDelete();
                return positionRepository.save(position);
            })
            .then();
    }
}
