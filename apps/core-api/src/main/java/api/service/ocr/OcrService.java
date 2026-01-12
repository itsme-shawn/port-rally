package api.service.ocr;

import api.domain.ocr.OcrDetectedPosition;
import api.domain.ocr.OcrResult;
import api.domain.ocr.UploadedImage;
import api.dto.portfolio.DetectedPositionDto;
import api.dto.portfolio.ImageUploadResponse;
import api.enums.ocr.OcrStatus;
import api.enums.ocr.UploadStatus;
import api.repository.ocr.OcrDetectedPositionRepository;
import api.repository.ocr.OcrResultRepository;
import api.repository.ocr.UploadedImageRepository;
import api.repository.asset.AssetRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.codec.multipart.FilePart;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

/**
 * OCR 이미지 분석 서비스
 * 현재는 Mock 데이터를 반환하며, 추후 실제 OCR/LLM 연동 예정
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OcrService {

    private final UploadedImageRepository uploadedImageRepository;
    private final OcrResultRepository ocrResultRepository;
    private final OcrDetectedPositionRepository detectedPositionRepository;
    private final AssetRepository assetRepository;

    // 임시 파일 저장 경로 (추후 S3로 교체 예정)
    private static final String TEMP_UPLOAD_DIR = System.getProperty("java.io.tmpdir") + "/portfolio-uploads";

    /**
     * 이미지 파일을 업로드하고 OCR 분석을 수행
     */
    public Mono<UploadedImage> uploadAndAnalyze(UUID userId, UUID portfolioId, FilePart filePart) {
        return saveFileToDisk(filePart)
            .flatMap(fileInfo -> {
                UploadedImage uploadedImage = UploadedImage.builder()
                    .userId(userId)
                    .portfolioId(portfolioId)
                    .storageUrl(fileInfo.filePath)
                    .uploadStatus(UploadStatus.PENDING)
                    .contentType(fileInfo.contentType)
                    .fileSize(fileInfo.fileSize)
                    .hashSha256(fileInfo.hash)
                    .retentionPolicy("90_DAYS")
                    .retainUntil(Instant.now().plusSeconds(90 * 24 * 60 * 60))
                    .build();

                return uploadedImageRepository.save(uploadedImage)
                    .doOnNext(saved -> log.info("이미지 저장 완료 - imageId: {}, path: {}", saved.getImageId(), saved.getStorageUrl()))
                    .flatMap(saved -> {
                        saved.markProcessing();
                        return uploadedImageRepository.save(saved)
                            .flatMap(processing -> performMockOcrAnalysis(processing)
                                .doOnSuccess(v -> log.info("OCR 분석 완료 - imageId: {}", processing.getImageId()))
                                .thenReturn(processing));
                    })
                    .flatMap(processing -> {
                        processing.markCompleted();
                        return uploadedImageRepository.save(processing);
                    });
            });
    }

    /**
     * 파일을 디스크에 저장 (Non-blocking)
     */
    private Mono<FileInfo> saveFileToDisk(FilePart filePart) {
        return Mono.fromCallable(() -> {
            Path uploadDir = Paths.get(TEMP_UPLOAD_DIR);
            if (!Files.exists(uploadDir)) {
                Files.createDirectories(uploadDir);
            }
            return uploadDir;
        })
        .subscribeOn(Schedulers.boundedElastic())
        .flatMap(uploadDir -> {
            String originalFilename = filePart.filename();
            String uniqueFilename = UUID.randomUUID() + "_" + originalFilename;
            Path filePath = uploadDir.resolve(uniqueFilename);

            return filePart.transferTo(filePath)
                .then(Mono.defer(() -> {
                    try {
                        long fileSize = Files.size(filePath);
                        String hash = calculateSHA256(filePath);
                        var contentTypeHeader = filePart.headers().getContentType();
                        String contentType = contentTypeHeader != null
                            ? contentTypeHeader.toString()
                            : "application/octet-stream";

                        log.info("파일 저장 완료 - path: {}, size: {} bytes", filePath, fileSize);
                        return Mono.just(new FileInfo(filePath.toString(), fileSize, contentType, hash));
                    } catch (IOException e) {
                        return Mono.error(e);
                    }
                }).subscribeOn(Schedulers.boundedElastic()));
        });
    }

    private String calculateSHA256(Path filePath) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] fileBytes = Files.readAllBytes(filePath);
            byte[] hashBytes = digest.digest(fileBytes);

            StringBuilder sb = new StringBuilder();
            for (byte b : hashBytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException | IOException e) {
            log.error("SHA-256 해시 계산 실패", e);
            return null;
        }
    }

    private Mono<OcrResult> performMockOcrAnalysis(UploadedImage uploadedImage) {
        OcrResult ocrResult = OcrResult.builder()
            .imageId(uploadedImage.getImageId())
            .status(OcrStatus.PENDING)
            .rawText("Mock OCR Raw Text: 삼성전자 10주, SK하이닉스 5주")
            .parsedData(io.r2dbc.postgresql.codec.Json.of("{\"detected_count\": 3}"))
            .build();

        return ocrResultRepository.save(ocrResult)
            .flatMap(savedResult -> 
                createMockDetectedPositions(savedResult.getOcrResultId())
                    .flatMap(mockPositions -> 
                        detectedPositionRepository.saveAll(mockPositions)
                            .collectList()
                            .doOnNext(positions -> log.info("Mock 종목 {} 개 생성 완료", positions.size()))
                    )
                    .thenReturn(savedResult)
            );
    }

    private Mono<List<OcrDetectedPosition>> createMockDetectedPositions(UUID ocrResultId) {
        var mockItems = List.of(
            new MockItem("005930", "삼성전자", "10", "70000", "키움증권"),
            new MockItem("000660", "SK하이닉스", "5", "130000", "토스증권"),
            new MockItem("035720", "카카오", "15", "45000", "KB증권"),
            new MockItem(null, "애플", "1", "300000", "해외주식") // 심볼 없는 케이스 테스트
        );

        return Flux.fromIterable(mockItems)
            .flatMap(item -> 
                // 1단계: 한글 이름으로 검색
                assetRepository.findFirstByNameKo(item.name())
                    // 2단계: (검색 결과 없으면) 영어 이름으로 검색
                    .switchIfEmpty(assetRepository.findFirstByNameEn(item.name()))
                    // 3단계: (검색 결과 없으면) 심볼로 검색 (심볼이 있을 때만)
                    .switchIfEmpty(Mono.justOrEmpty(item.symbol())
                        .flatMap(symbol -> assetRepository.findBySymbol(symbol)))
                    // 매칭 성공 시 데이터 매핑
                    .map(asset -> OcrDetectedPosition.builder()
                        .ocrResultId(ocrResultId)
                        .detectedSymbol(item.symbol() != null ? item.symbol() : asset.getSymbol())
                        .detectedName(asset.getNameKo())
                        .detectedMarket(asset.getMarket())
                        .quantity(new BigDecimal(item.qty()))
                        .averageCost(new BigDecimal(item.avg()))
                        .currency(asset.getCurrency())
                        .purchaseDate(java.time.LocalDate.now().minusDays(30))
                        .broker(item.broker())
                        .matchAssetId(asset.getAssetId())
                        .matchConfidence(new BigDecimal("0.98"))
                        .isConfirmed(false)
                        .build()
                    )
                    // 4단계: 모든 단계 실패 시 예외 처리용 객체 반환
                    .defaultIfEmpty(
                        OcrDetectedPosition.builder()
                            .ocrResultId(ocrResultId)
                            .detectedSymbol(item.symbol())
                            .detectedName(item.name())
                            .detectedMarket("UNKNOWN")
                            .quantity(new BigDecimal(item.qty()))
                            .averageCost(new BigDecimal(item.avg()))
                            .currency("KRW")
                            .matchAssetId(null)
                            .matchConfidence(new BigDecimal("0.30"))
                            .isConfirmed(false)
                            .build()
                    )
            )
            .collectList();
    }

    public Mono<OcrResult> getOcrResult(UUID imageId) {
        return ocrResultRepository.findByImageId(imageId);
    }

    public Flux<OcrDetectedPosition> getDetectedPositions(UUID ocrResultId) {
        return detectedPositionRepository.findAllByOcrResultId(ocrResultId);
    }

    public Mono<ImageUploadResponse> uploadAnalyzeAndGetResult(UUID userId, UUID portfolioId, FilePart filePart) {
        return uploadAndAnalyze(userId, portfolioId, filePart)
            .flatMap(uploadedImage ->
                getOcrResult(uploadedImage.getImageId())
                    .zipWhen(ocrResult ->
                        getDetectedPositions(ocrResult.getOcrResultId())
                            .map(DetectedPositionDto::from)
                            .collectList()
                    )
                    .map(tuple -> ImageUploadResponse.of(
                        uploadedImage.getImageId(),
                        tuple.getT1().getOcrResultId(),
                        tuple.getT2()
                    ))
            );
    }

    private record MockItem(String symbol, String name, String qty, String avg, String broker) {}

    private static class FileInfo {
        String filePath;
        long fileSize;
        String contentType;
        String hash;

        FileInfo(String filePath, long fileSize, String contentType, String hash) {
            this.filePath = filePath;
            this.fileSize = fileSize;
            this.contentType = contentType;
            this.hash = hash;
        }
    }
}