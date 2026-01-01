package api.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.r2dbc.config.EnableR2dbcAuditing;
import org.springframework.data.r2dbc.repository.config.EnableR2dbcRepositories;

/**
 * R2DBC 설정
 * - Spring Data R2DBC 기본 Enum 변환 사용 (Enum.name() ↔ String)
 * - DB는 VARCHAR, 별도 Converter 불필요
 */
@Configuration // springboot가 자동으로 감지
@EnableR2dbcAuditing // CreateDate, LastModifiedDate 자동 설정
@EnableR2dbcRepositories(basePackages = "api.repository")
public class R2dbcConfig {
    // Spring Boot auto-configuration이 ConnectionFactory와 기본 변환 제공
}
