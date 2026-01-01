#!/bin/bash
# 로컬 Spring Boot 실행 스크립트
# Docker의 postgres, redis에 연결

cd "$(dirname "$0")"

# .env 파일 로드
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded .env"
else
    echo "Warning: .env file not found"
fi

cd apps/core-api
./gradlew bootRun --args='--spring.profiles.active=local'
