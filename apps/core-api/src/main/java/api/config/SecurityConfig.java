package api.config;

import api.security.handler.LoggingServerAccessDeniedHandler;
import api.security.handler.LoggingServerAuthenticationEntryPoint;
import api.security.handler.OAuth2AuthenticationFailureHandler;
import api.security.jwt.JwtAuthenticationFilter;
import api.security.handler.OAuth2AuthenticationSuccessHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableReactiveMethodSecurity;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.SecurityWebFiltersOrder;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.web.server.SecurityWebFilterChain;
import org.springframework.security.web.server.context.NoOpServerSecurityContextRepository;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsConfigurationSource;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

// OAuth2 + JWT 보안 설정
@Configuration
@EnableWebFluxSecurity
@EnableReactiveMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final OAuth2AuthenticationSuccessHandler successHandler;
    private final OAuth2AuthenticationFailureHandler failureHandler;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final LoggingServerAuthenticationEntryPoint authenticationEntryPoint;
    private final LoggingServerAccessDeniedHandler accessDeniedHandler;

    @Bean
    public SecurityWebFilterChain springSecurityFilterChain(
            ServerHttpSecurity http,
            CorsConfigurationSource corsConfigurationSource) {
        return http
            .csrf(ServerHttpSecurity.CsrfSpec::disable)
            .cors(corsSpec -> corsSpec.configurationSource(corsConfigurationSource))
            .authorizeExchange(exchanges -> exchanges
                .pathMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                .pathMatchers("/oauth2/**", "/login/oauth2/**").permitAll()
                .pathMatchers("/auth/refresh").permitAll()
                .pathMatchers("/api/v1/auth/dev/**").permitAll() // ⚠️ 개발용 토큰 발급 엔드포인트

                // PENDING 상태 사용자도 접근 가능한 엔드포인트
                .pathMatchers("/api/v1/terms").authenticated()  // 약관 목록 조회
                .pathMatchers("/api/v1/auth/signup/complete").authenticated()  // 회원가입 완료
                .pathMatchers("/api/v1/auth/me").authenticated()  // 사용자 정보 조회
                .pathMatchers("/api/v1/auth/logout").authenticated()  // 로그아웃
                .pathMatchers("/api/v1/auth/withdraw").authenticated()  // 회원 탈퇴

				// TODO : 추후 해제 (ACTIVE 상태만 접근 가능하도록 설정)
                // .pathMatchers("/auth/**").authenticated()
                // .pathMatchers("/api/**").authenticated()
                .anyExchange().permitAll()
            )
            .oauth2Login(oauth2 -> oauth2
                .authenticationSuccessHandler(successHandler)
                .authenticationFailureHandler(failureHandler)
            )
            .addFilterAfter(jwtAuthenticationFilter, SecurityWebFiltersOrder.OAUTH2_AUTHORIZATION_CODE)
            .exceptionHandling(exceptionHandlingSpec -> exceptionHandlingSpec
                .authenticationEntryPoint(authenticationEntryPoint)
                .accessDeniedHandler(accessDeniedHandler)
            )
            .securityContextRepository(NoOpServerSecurityContextRepository.getInstance())
            .httpBasic(ServerHttpSecurity.HttpBasicSpec::disable)
            .formLogin(ServerHttpSecurity.FormLoginSpec::disable)
            .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource(
            @Value("${cors.allowed-origins:http://localhost:3000}") String allowedOrigins) {
        List<String> origins = Arrays.stream(allowedOrigins.split(","))
            .map(String::trim)
            .filter(origin -> !origin.isEmpty())
            .collect(Collectors.toList());

        CorsConfiguration config = new CorsConfiguration();
        config.setAllowCredentials(true);
        config.setAllowedOriginPatterns(origins);
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        config.setAllowedHeaders(List.of("*"));
        config.setExposedHeaders(List.of("Set-Cookie", "Authorization", "X-Refresh-Token"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
