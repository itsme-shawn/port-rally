#!/bin/bash

# .env 파일 로드 (환경 변수 설정)
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env"
fi

# 기본값 설정
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

echo "=========================================="
echo "   🚀 Redis Init/Reset Script"
echo "=========================================="
echo "Target Redis: $REDIS_HOST:$REDIS_PORT"

# 실행 중인 Redis 컨테이너 ID 찾기
CONTAINER_ID=$(docker compose -f docker-compose.dev.yml ps -q redis)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Redis container is not running."
    echo "👉 Please start it with 'docker compose up -d redis'."
    exit 1
fi

echo "Found Redis container: $CONTAINER_ID"
echo "⚠️  WARNING: This will FLUSH ALL DATA from Redis!"
echo "Are you sure you want to continue? (y/N)"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "🔄 Resetting Redis data..."

# redis-cli를 사용하여 데이터 전체 삭제 (FLUSHALL)
docker exec -i "$CONTAINER_ID" redis-cli FLUSHALL

if [ $? -eq 0 ]; then
    echo "✅ Redis initialized/reset successfully!"
    echo "All keys have been removed."
else
    echo "❌ Failed to reset Redis."
    exit 1
fi
