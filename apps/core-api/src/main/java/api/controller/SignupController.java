package api.controller;

import api.dto.auth.SignupCompleteRequest;
import api.dto.auth.SignupCompleteResponse;
import api.dto.portfolio.DetectedPositionDto;
import api.exception.AuthException;
import api.security.principal.UserPrincipal;
import api.service.auth.SignupService;
import api.service.ocr.OcrService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.http.codec.multipart.FilePart;
import org.springframework.core.io.buffer.DataBufferUtils;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "Signup", description = "회원가입 API")
public class SignupController {

    private final SignupService signupService;
    private final OcrService ocrService;

    @PostMapping(path = "/signup/upload-portfolio", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.OK)
    @Operation(
        summary = "포트폴리오 이미지 업로드 (OCR)",
        description = "포트폴리오 스크린샷 이미지를 업로드하여 보유 종목을 인식합니다."
    )
    public Mono<List<DetectedPositionDto>> uploadPortfolioImage(
        @AuthenticationPrincipal UserPrincipal principal,
        @RequestPart("file") Mono<FilePart> filePartMono) {

        if (principal == null) {
            return Mono.error(new AuthException("Unauthorized"));
        }
        
        // 임시 디렉토리 경로 설정
        Path tempDir = Paths.get(System.getProperty("java.io.tmpdir"));

        return filePartMono.flatMap(filePart -> {
            // 임시 파일 생성
            Path tempFile = tempDir.resolve(UUID.randomUUID() + "-" + filePart.filename());
            
            // 파일을 임시 저장
            return filePart.transferTo(tempFile)
                .then(Mono.defer(() -> {
                    log.info("임시 파일 저장 성공: {}", tempFile);
                    // OCR 서비스 호출
                    return ocrService.processPortfolioImage(tempFile);
                }))
                .doOnTerminate(() -> {
                    // 작업 완료 후 임시 파일 삭제
                    try {
                        Files.deleteIfExists(tempFile);
                        log.info("임시 파일 삭제 성공: {}", tempFile);
                    } catch (IOException e) {
                        log.error("임시 파일 삭제 실패: {}", tempFile, e);
                    }
                });
        });
    }

    @PostMapping("/signup/complete")
    @ResponseStatus(HttpStatus.OK)
    @Operation(
        summary = "회원가입 완료",
        description = "약관 동의를 통해 회원가입을 완료합니다. PENDING 상태의 사용자만 호출 가능합니다."
    )
    public Mono<SignupCompleteResponse> completeSignup(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody SignupCompleteRequest request,
            ServerWebExchange exchange) {

        if (principal == null) {
            return Mono.error(new AuthException("Unauthorized"));
        }

        // 클라이언트 IP 주소 추출
        String ipAddress = extractIpAddress(exchange);

        // User-Agent 추출
        String userAgent = exchange.getRequest().getHeaders().getFirst("User-Agent");

        return signupService.completeSignup(
            principal.getUserId(),
            request,
            ipAddress,
            userAgent
        );
    }

    private String extractIpAddress(ServerWebExchange exchange) {
        // X-Forwarded-For 헤더 확인 (프록시/로드밸런서 뒤에 있을 경우)
        String forwardedFor = exchange.getRequest().getHeaders().getFirst("X-Forwarded-For");
        if (StringUtils.hasText(forwardedFor)) {
            return forwardedFor.split(",")[0].trim();
        }

        // X-Real-IP 헤더 확인
        String realIp = exchange.getRequest().getHeaders().getFirst("X-Real-IP");
        if (StringUtils.hasText(realIp)) {
            return realIp;
        }

        // Remote Address 사용
        var remoteAddress = exchange.getRequest().getRemoteAddress();
        if (remoteAddress != null && remoteAddress.getAddress() != null) {
            return remoteAddress.getAddress().getHostAddress();
        }
        return "unknown";
    }
}
