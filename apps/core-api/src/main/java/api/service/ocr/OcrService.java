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
import api.service.ocr.parser.PortfolioParser;
import api.util.FuzzyMatcher;
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
 * OCR 이미지 분석 서비스 (Tesseract 사용)
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OcrService {

    private final UploadedImageRepository uploadedImageRepository;
    private final OcrResultRepository ocrResultRepository;
    private final OcrDetectedPositionRepository detectedPositionRepository;
    private final AssetRepository assetRepository;
    private final TesseractOcrProcessor tesseractOcrProcessor;
    private final PortfolioParser portfolioParser;

    // 임시 파일 저장 경로 (추후 S3로 교체 예정)
    private static final String TEMP_UPLOAD_DIR = System.getProperty("java.io.tmpdir") + "/portfolio-uploads";

    // OCR 매칭 신뢰도 임계값 (0.85 이상만 자동 매칭)
    private static final double MATCH_CONFIDENCE_THRESHOLD = 0.85;

    /**
     * 이미지 파일 경로로부터 직접 OCR 분석을 수행 (SignupController 용)
     */
    public Mono<List<DetectedPositionDto>> processPortfolioImage(Path imagePath) {
        return tesseractOcrProcessor.process(imagePath)
            .flatMap(ocrProcessResult -> {
                String rawText = ocrProcessResult.extractedText();
                var parsedPositions = portfolioParser.parse(rawText);

                log.info("OCR 처리 완료 - confidence: {}, parsed: {} positions",
                    ocrProcessResult.confidence(), parsedPositions.size());

                return Flux.fromIterable(parsedPositions)
                    .flatMap(parsed -> {
                        String symbol = parsed.symbol();
                        String name = parsed.name();

                        return assetRepository.findFirstByNameKo(name)
                            .switchIfEmpty(assetRepository.findFirstByNameEn(name))
                            .switchIfEmpty(Mono.justOrEmpty(symbol)
                                .flatMap(assetRepository::findBySymbol))
                            .map(asset -> {
                                // Fuzzy matching으로 신뢰도 계산
                                double nameConfidence = FuzzyMatcher.calculateSimilarity(name, asset.getNameKo());
                                double symbolConfidence = symbol != null
                                    ? FuzzyMatcher.calculateSimilarity(symbol, asset.getSymbol())
                                    : 0.0;
                                double confidence = Math.max(nameConfidence, symbolConfidence);

                                // 신뢰도가 임계값 이상인 경우만 자동 매칭
                                if (confidence >= MATCH_CONFIDENCE_THRESHOLD) {
                                    log.info("High confidence match - OCR: {}, DB: {}, confidence: {:.2f}",
                                        name, asset.getNameKo(), confidence);
                                    return DetectedPositionDto.builder()
                                        .detectedPositionId(UUID.randomUUID())
                                        .symbol(symbol != null ? symbol : asset.getSymbol())
                                        .name(name)
                                        .market(asset.getMarket())
                                        .quantity(parseBigDecimal(parsed.quantity()))
                                        .averageCost(parseBigDecimal(parsed.averageCost()))
                                        .currency(parsed.currency() != null ? parsed.currency() : asset.getCurrency())
                                        .assetId(asset.getAssetId())
                                        .matchConfidence(confidence)
                                        .build();
                                } else {
                                    log.warn("Low confidence match rejected - OCR: {}, DB: {}, confidence: {:.2f} (threshold: {:.2f})",
                                        name, asset.getNameKo(), confidence, MATCH_CONFIDENCE_THRESHOLD);
                                    return DetectedPositionDto.builder()
                                        .detectedPositionId(UUID.randomUUID())
                                        .symbol(symbol)
                                        .name(name)
                                        .market("UNKNOWN")
                                        .quantity(parseBigDecimal(parsed.quantity()))
                                        .averageCost(parseBigDecimal(parsed.averageCost()))
                                        .currency(parsed.currency() != null ? parsed.currency() : "KRW")
                                        .assetId(null)
                                        .matchConfidence(confidence)
                                        .note(String.format("매칭 신뢰도 부족 (%.2f%% < %.2f%%)", confidence * 100, MATCH_CONFIDENCE_THRESHOLD * 100))
                                        .build();
                                }
                            })
                            .defaultIfEmpty(DetectedPositionDto.builder()
                                .detectedPositionId(UUID.randomUUID())
                                .symbol(symbol)
                                .name(name)
                                .market("UNKNOWN")
                                .quantity(parseBigDecimal(parsed.quantity()))
                                .averageCost(parseBigDecimal(parsed.averageCost()))
                                .currency(parsed.currency() != null ? parsed.currency() : "KRW")
                                .assetId(null)
                                .matchConfidence(0.0)
                                .note("종목 정보를 찾을 수 없습니다.")
                                .build());
                    })
                    .collectList();
            })
            .onErrorResume(e -> {
                log.error("OCR 처리 실패: {}", e.getMessage(), e);
                return Mono.just(List.of());
            });
    }

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
                            .flatMap(processing -> performOcrAnalysis(processing)
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

    /**
     * Tesseract OCR을 사용하여 이미지를 분석합니다.
     */
    private Mono<OcrResult> performOcrAnalysis(UploadedImage uploadedImage) {
        return Mono.fromCallable(() -> Paths.get(uploadedImage.getStorageUrl()))
            .subscribeOn(Schedulers.boundedElastic())
            .flatMap(imagePath -> tesseractOcrProcessor.process(imagePath)
                .flatMap(ocrProcessResult -> {
                    String rawText = ocrProcessResult.extractedText();
                    var parsedPositions = portfolioParser.parse(rawText);

                    log.info("OCR 추출 완료 - confidence: {}, text length: {}, parsed: {} positions",
                        ocrProcessResult.confidence(), rawText.length(), parsedPositions.size());

                    OcrResult ocrResult = OcrResult.builder()
                        .imageId(uploadedImage.getImageId())
                        .status(OcrStatus.PENDING)
                        .rawText(rawText)
                        .parsedData(io.r2dbc.postgresql.codec.Json.of(
                            String.format("{\"detected_count\": %d, \"confidence\": %.2f}",
                                parsedPositions.size(), ocrProcessResult.confidence())
                        ))
                        .build();

                    return ocrResultRepository.save(ocrResult)
                        .flatMap(savedResult ->
                            createDetectedPositionsFromParsed(savedResult.getOcrResultId(), parsedPositions)
                                .flatMap(positions ->
                                    detectedPositionRepository.saveAll(positions)
                                        .collectList()
                                        .doOnNext(saved -> log.info("종목 {} 개 저장 완료", saved.size()))
                                )
                                .thenReturn(savedResult)
                        );
                })
                .onErrorResume(e -> {
                    log.error("OCR 처리 실패: {}", e.getMessage(), e);
                    OcrResult errorResult = OcrResult.builder()
                        .imageId(uploadedImage.getImageId())
                        .status(OcrStatus.FAILED)
                        .rawText("OCR 처리 실패: " + e.getMessage())
                        .parsedData(io.r2dbc.postgresql.codec.Json.of("{\"error\": \"OCR failed\"}"))
                        .build();
                    return ocrResultRepository.save(errorResult);
                })
            );
    }

    /**
     * 파싱된 포지션을 OcrDetectedPosition으로 변환하고 자산 매칭을 수행합니다.
     * Fuzzy matching을 사용하여 유사도를 계산합니다.
     */
    private Mono<List<OcrDetectedPosition>> createDetectedPositionsFromParsed(
            UUID ocrResultId,
            List<PortfolioParser.ParsedPosition> parsedPositions) {

        return Flux.fromIterable(parsedPositions)
            .flatMap(parsed -> {
                String symbol = parsed.symbol();
                String name = parsed.name();

                // 1단계: 한글 이름으로 검색
                return assetRepository.findFirstByNameKo(name)
                    // 2단계: 영어 이름으로 검색
                    .switchIfEmpty(assetRepository.findFirstByNameEn(name))
                    // 3단계: 심볼로 검색 (심볼이 있을 때만)
                    .switchIfEmpty(Mono.justOrEmpty(symbol)
                        .flatMap(assetRepository::findBySymbol))
                    // 매칭 성공 시 유사도 계산
                    .map(asset -> {
                        // Fuzzy matching으로 신뢰도 계산
                        double nameConfidence = FuzzyMatcher.calculateSimilarity(name, asset.getNameKo());
                        double symbolConfidence = symbol != null
                            ? FuzzyMatcher.calculateSimilarity(symbol, asset.getSymbol())
                            : 0.0;

                        // 최고 유사도 선택
                        double confidence = Math.max(nameConfidence, symbolConfidence);

                        // 신뢰도가 임계값 이상인 경우만 자동 매칭
                        if (confidence >= MATCH_CONFIDENCE_THRESHOLD) {
                            log.info("High confidence match - OCR: {}, DB: {}, confidence: {:.2f}",
                                name, asset.getNameKo(), confidence);
                            return OcrDetectedPosition.builder()
                                .ocrResultId(ocrResultId)
                                .detectedSymbol(symbol != null ? symbol : asset.getSymbol())
                                .detectedName(name)
                                .detectedMarket(asset.getMarket())
                                .quantity(parseBigDecimal(parsed.quantity()))
                                .averageCost(parseBigDecimal(parsed.averageCost()))
                                .currency(parsed.currency() != null ? parsed.currency() : asset.getCurrency())
                                .matchAssetId(asset.getAssetId())
                                .matchConfidence(confidence)
                                .isConfirmed(false)
                                .build();
                        } else {
                            log.warn("Low confidence match rejected - OCR: {}, DB: {}, confidence: {:.2f} (threshold: {:.2f})",
                                name, asset.getNameKo(), confidence, MATCH_CONFIDENCE_THRESHOLD);
                            return OcrDetectedPosition.builder()
                                .ocrResultId(ocrResultId)
                                .detectedSymbol(symbol)
                                .detectedName(name)
                                .detectedMarket("UNKNOWN")
                                .quantity(parseBigDecimal(parsed.quantity()))
                                .averageCost(parseBigDecimal(parsed.averageCost()))
                                .currency(parsed.currency() != null ? parsed.currency() : "KRW")
                                .matchAssetId(null)
                                .matchConfidence(confidence)
                                .isConfirmed(false)
                                .note(String.format("매칭 신뢰도 부족 (%.2f%% < %.2f%%)", confidence * 100, MATCH_CONFIDENCE_THRESHOLD * 100))
                                .build();
                        }
                    })
                    .onErrorResume(e -> {
                        log.error("종목 검색 중 오류: name={}, symbol={}", name, symbol, e);
                        return Mono.empty();
                    })
                    // 매칭 실패 시
                    .defaultIfEmpty(
                        OcrDetectedPosition.builder()
                            .ocrResultId(ocrResultId)
                            .detectedSymbol(symbol)
                            .detectedName(name)
                            .detectedMarket("UNKNOWN")
                            .quantity(parseBigDecimal(parsed.quantity()))
                            .averageCost(parseBigDecimal(parsed.averageCost()))
                            .currency(parsed.currency() != null ? parsed.currency() : "KRW")
                            .matchAssetId(null)
                            .matchConfidence(0.0)
                            .isConfirmed(false)
                            .note("종목 정보를 찾을 수 없습니다.")
                            .build()
                    );
            })
            .collectList();
    }

    private BigDecimal parseBigDecimal(String value) {
        try {
            return value != null && !value.trim().isEmpty()
                ? new BigDecimal(value.trim().replace(",", ""))
                : BigDecimal.ZERO;
        } catch (NumberFormatException e) {
            log.warn("숫자 변환 실패: {}", value);
            return BigDecimal.ZERO;
        }
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
                        tuple.getT1().getOcrResultId(),
                        tuple.getT2()
                    ))
            );
    }

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