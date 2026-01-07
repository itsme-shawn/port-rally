package api.config;

import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.oas.models.responses.ApiResponses;
import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
public class OpenApiConfig {

	// Swagger에 google login redirect 엔드포인트를 수동 노출 (spring security에서 제공해서 기본적으로는 swagger 노출 안 됨)
    @Bean
    public OpenApiCustomizer oauth2AuthorizationEndpointCustomiser() {
        return openApi -> {
            Operation operation = new Operation()
                .summary("Start Google OAuth2 login")
                .description("Redirects to Google OAuth2 authorization endpoint")
                .addTagsItem("Auth")
                .responses(new ApiResponses()
                    .addApiResponse("302", new ApiResponse().description("Redirect to Google")));

            openApi.path("/oauth2/authorization/google", new PathItem().get(operation));
        };
    }
}
