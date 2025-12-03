# Build stage
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . /app
RUN chmod +x gradlew && ./gradlew bootJar --no-daemon

# Run stage
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/build/libs/*.jar /app/app.jar
EXPOSE 8080
# 8080 포트를 썼다고 알려만줄 뿐 실제로 동작하는건 아님
ENTRYPOINT ["java","-jar","/app/app.jar"]
