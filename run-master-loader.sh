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

# 로컬 실행 시 DB_HOST는 localhost여야 함 (Docker 외부에서 실행하므로)
export DB_HOST=localhost

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

# market-data 서비스 디렉토리로 이동
cd "$(dirname "$0")/services/market-data"

echo "Starting Master Loader (Target DB: $DB_HOST)..."

# PYTHONPATH 설정 및 실행
if command -v uv &> /dev/null; then
    PYTHONPATH=src uv run src/quote_pipeline/loader/master_loader.py
else
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    python3 src/quote_pipeline/loader/master_loader.py
fi

echo "✅ Master Loader completed successfully!"
