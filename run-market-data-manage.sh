#!/bin/bash
set -e

# Root .env 파일 로드
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env"
fi

# Market Data .env 파일 로드
if [ -f "services/market-data/.env" ]; then
    export $(cat services/market-data/.env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from services/market-data/.env"
fi

# 로컬 실행을 위한 환경변수 오버라이드
# Docker 네트워크 외부(호스트)에서 Docker 내부 서비스에 접근하므로 localhost를 사용함
export DB_HOST=localhost
export REDIS_URL=redis://localhost:6379/0

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

check_connection "$DB_HOST" "5432" "PostgreSQL"
# Extract host and port from REDIS_URL or just use localhost:6379 since it is hardcoded above
check_connection "localhost" "6379" "Redis"

# market-data 서비스 디렉토리로 이동
cd "$(dirname "$0")/services/market-data"

echo "Starting Market Data Manage Tool (Target Redis: $REDIS_URL, Target DB: $DB_HOST)..."

# PYTHONPATH 설정 및 실행 (uv 사용 권장)
if command -v uv &> /dev/null; then
    PYTHONPATH=src uv run -m quote_pipeline.manage "$@"
else
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    python3 -m quote_pipeline.manage "$@"
fi
