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

# Function to check connection
check_connection() {
    local host=$1
    local port=$2
    local name=$3
    echo "Checking $name connection at $host:$port..."
    if python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2); s.connect(('$host', int('$port'))); s.close()" 2>/dev/null; then
        echo "✅ Connected to $name at $host:$port"
    else
        echo "❌ Failed to connect to $name at $host:$port"
        echo "   Please ensure $name is running (e.g., docker-compose up -d)"
        exit 1
    fi
}

# Default to localhost if not set
DB_HOST=localhost
DB_PORT=${DB_PORT:-5432}
REDIS_HOST=localhost
REDIS_PORT=${REDIS_PORT:-6379}

check_connection "$DB_HOST" "$DB_PORT" "PostgreSQL"
check_connection "$REDIS_HOST" "$REDIS_PORT" "Redis"

cd apps/core-api
# APP_ENV가 설정되어 있으면 그것을 사용, 없으면 local을 기본값으로 사용
PROFILE="${APP_ENV:-local}"
echo "Starting Spring Boot with profile: ${PROFILE}"
./gradlew bootRun --args="--spring.profiles.active=${PROFILE}"
