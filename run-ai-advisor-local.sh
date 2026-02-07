#!/bin/bash
set -e

# Root .env 파일 로드
if [ -f ".env.local" ]; then
    export $(cat .env.local | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env.local"
elif [ -f ".env.dev" ]; then
    export $(cat .env.dev | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env.dev"
fi
    
# Set PORT from AI_ADVISOR_PORT if available
if [ -n "$AI_ADVISOR_PORT" ]; then
    export PORT=$AI_ADVISOR_PORT
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

check_connection "$DB_HOST" "$DB_PORT" "PostgreSQL"
check_connection "$REDIS_HOST" "$REDIS_PORT" "Redis"

# Check Google API Key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY is not set"
    echo "   Please set GOOGLE_API_KEY in .env.dev or .env.local"
    exit 1
fi

echo "✅ GOOGLE_API_KEY is set (${GOOGLE_API_KEY:0:20}...)"

# ai-advisor 서비스 디렉토리로 이동
cd "services/ai-advisor"

# DATABASE_URL 구성
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
export REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
export LOG_LEVEL="${AI_SERVICE_LOG_LEVEL:-INFO}"

echo "Starting AI Advisor locally..."
echo "  Target PostgreSQL: $DB_HOST:$DB_PORT/$DB_NAME"
echo "  Target Redis: $REDIS_HOST:$REDIS_PORT/$REDIS_DB"
echo "  Gemini Model: gemini-1.5-flash-latest"
echo "  Port: ${PORT:-8081}"

# PYTHONPATH 설정 및 실행 (uv 사용 권장)
if command -v uv &> /dev/null; then
    PYTHONPATH=src uv run python -m advisor.main "$@"
else
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    python3 -m advisor.main "$@"
fi
