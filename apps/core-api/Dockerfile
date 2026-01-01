# Build stage
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app

# Gradle wrapper 및 설정 파일 먼저 복사 (캐시 최적화)
COPY gradlew settings.gradle build.gradle ./
COPY gradle ./gradle

# 의존성 먼저 다운로드 (캐시 레이어)
RUN chmod +x gradlew && ./gradlew dependencies --no-daemon || true

# 소스 코드 복사 후 빌드
COPY src ./src
RUN ./gradlew bootJar --no-daemon -x test

# Run stage
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

# 보안: non-root 사용자로 실행
RUN addgroup -g 1001 appgroup && adduser -u 1001 -G appgroup -D appuser
USER appuser

COPY --from=build /app/build/libs/*.jar /app/app.jar

EXPOSE 8080

# JVM 옵션 (컨테이너 환경 최적화)
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
