package api.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
// OAuth2 리다이렉트 임시 엔드포인트 (프론트엔드 개발 전까지 사용)
// 실제 프론트엔드에서는 /api/v1/auth/me 를 호출하여 사용자 정보를 조회해야 함
public class OAuth2CallbackController {

    @GetMapping(value = "/callback", produces = MediaType.TEXT_HTML_VALUE)
    public Mono<String> callback() {
        // OAuth2 성공 후 리다이렉트되는 페이지
        // 쿠키에 httpOnly로 토큰이 설정되어 있으므로 /api/v1/auth/me 호출 안내
        log.info("OAuth2 callback - Redirected to callback page");
        return Mono.just(buildSuccessHtml());
    }

    @GetMapping(value = "/error", produces = MediaType.TEXT_HTML_VALUE)
    public Mono<String> error(
            @RequestParam(required = false) String error,
            @RequestParam(required = false) String error_description) {

        log.error("OAuth2 error - error: {}, description: {}", error, error_description);

        String errorMessage = error != null ? error : "Unknown error";
        String errorDesc = error_description != null ? error_description : "No description provided";

        return Mono.just(buildErrorHtml(errorMessage, errorDesc));
    }

    private String buildSuccessHtml() {
        return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth2 Login Success</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto; }
                    h1 { color: #28a745; }
                    .token-info { background: #e8f5e9; padding: 15px; border-radius: 4px; margin-top: 20px; }
                    .refresh-test { background: #fff3cd; padding: 15px; border-radius: 4px; margin-top: 20px; }
                    .refresh-test button { padding: 8px 12px; border: 1px solid #c0ca33; background: #f9fbe7; cursor: pointer; border-radius: 4px; }
                    .refresh-test button:hover { background: #f0f4c3; }
                    .api-info { background: #e3f2fd; padding: 15px; border-radius: 4px; margin-top: 20px; }
                    .api-info code { background: #bbdefb; padding: 2px 6px; border-radius: 3px; }
                    .note { margin-top: 20px; color: #888; font-size: 13px; }
                    #user-info { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; display: none; }
                    .user-details { display: flex; align-items: center; gap: 15px; }
                    .profile-img { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; }
                    .error { color: #dc3545; }
                    .loading { color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Login Successful!</h1>

                    <div class="token-info">
                        <p><strong>Tokens are set in HttpOnly cookies:</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li><code>access_token</code> - JWT for authentication (HttpOnly)</li>
                            <li><code>refresh_token</code> - For token refresh (HttpOnly)</li>
                        </ul>
                    </div>

                    <div class="refresh-test">
                        <p><strong>Refresh 테스트:</strong></p>
                        <button id="refresh-button" type="button">/api/v1/auth/refresh 호출</button>
                        <p id="refresh-result" class="loading">아직 호출하지 않았습니다.</p>
                    </div>

                    <div class="api-info">
                        <p><strong>To get user info, call:</strong></p>
                        <p><code>GET /api/v1/auth/me</code></p>
                        <p style="font-size: 13px; color: #666; margin-top: 8px;">
                            The browser will automatically include the HttpOnly cookies.
                        </p>
                    </div>

                    <div id="user-info">
                        <p class="loading">Loading user info...</p>
                    </div>

                    <p class="note">
                        This is a temporary endpoint for testing.
                        In production, redirect to your frontend application.
                    </p>
                </div>

                <script>
                    // 자동으로 /api/v1/auth/me 호출하여 사용자 정보 표시
                    fetch('/api/v1/auth/me', { credentials: 'include' })
                        .then(res => {
                            if (!res.ok) throw new Error('Failed to fetch user info');
                            return res.json();
                        })
                        .then(user => {
                            const userInfoDiv = document.getElementById('user-info');
                            userInfoDiv.style.display = 'block';
                            userInfoDiv.innerHTML = `
                                <div class="user-details">
                                    ${user.profileImageUrl ? `<img src="${user.profileImageUrl}" alt="Profile" class="profile-img">` : ''}
                                    <div>
                                        <h3 style="margin: 0;">${user.displayName}</h3>
                                        <p style="margin: 5px 0; color: #666;">${user.email}</p>
                                        <p style="margin: 0; font-size: 12px; color: #888;">via ${user.provider}</p>
                                    </div>
                                </div>
                                <p style="margin-top: 10px; font-size: 13px; color: #666;">User ID: <code>${user.userId}</code></p>
                            `;
                        })
                        .catch(err => {
                            const userInfoDiv = document.getElementById('user-info');
                            userInfoDiv.style.display = 'block';
                            userInfoDiv.innerHTML = `<p class="error">Failed to load user info: ${err.message}</p>`;
                        });

                    // refresh 로직 테스트
                    const refreshButton = document.getElementById('refresh-button');
                    const refreshResult = document.getElementById('refresh-result');

                    refreshButton.addEventListener('click', () => {
                        refreshResult.textContent = '요청 중...';
                        fetch('/api/v1/auth/refresh', { method: 'POST', credentials: 'include' })
                            .then(async res => {
                                const text = await res.text();
                                let data = null;
                                try {
                                    data = text ? JSON.parse(text) : null;
                                } catch (e) {
                                    data = null;
                                }
                                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                                const expiresIn = data && data.expiresIn ? `, expiresIn=${data.expiresIn}` : '';
                                refreshResult.textContent = `성공${expiresIn}`;
                            })
                            .catch(err => {
                                refreshResult.textContent = `실패: ${err.message}`;
                            });
                    });
                </script>
            </body>
            </html>
            """;
    }

    private String buildErrorHtml(String errorMessage, String errorDesc) {
        return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth2 Login Failed</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto; }
                    h1 { color: #dc3545; }
                    .error-box { background: #fff3f3; padding: 15px; border-radius: 4px; border-left: 4px solid #dc3545; margin: 15px 0; }
                    .label { font-weight: bold; color: #333; }
                    .retry { margin-top: 20px; }
                    .retry a { color: #007bff; text-decoration: none; }
                    .retry a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Login Failed</h1>
                    <p>OAuth2 authentication failed.</p>

                    <div class="error-box">
                        <p class="label">Error:</p>
                        <p>%s</p>
                        <p class="label">Description:</p>
                        <p>%s</p>
                    </div>

                    <div class="retry">
                        <a href="/oauth2/authorization/google">Try again with Google</a>
                    </div>
                </div>
            </body>
            </html>
            """.formatted(escapeHtml(errorMessage), escapeHtml(errorDesc));
    }

    private String escapeHtml(String input) {
        if (input == null) return "";
        return input
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;");
    }

}
