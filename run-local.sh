#!/bin/bash
# 로컬 Spring Boot 실행 스크립트
# Docker의 postgres, redis에 연결

cd "$(dirname "$0")"

# Root .env 파일 로드
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded .env"
else
    echo "Warning: .env file not found"
fi

# Core API .env 파일 로드
if [ -f "apps/core-api/.env" ]; then
    export $(cat apps/core-api/.env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded apps/core-api/.env"
else
    echo "Warning: apps/core-api/.env file not found"
fi

cd apps/core-api
# APP_ENV가 설정되어 있으면 그것을 사용, 없으면 local을 기본값으로 사용
PROFILE="${APP_ENV:-local}"
echo "Starting Spring Boot with profile: ${PROFILE}"
./gradlew bootRun --args="--spring.profiles.active=${PROFILE}"
