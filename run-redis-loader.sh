#!/bin/bash
set -e

# Error handler
trap 'if [ $? -ne 0 ]; then echo "❌ Script exited with error."; fi' EXIT

# Robust .env loader
load_env() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        echo "Loading $env_file..."
        # Read file line by line
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ "$line" =~ ^# ]] || [[ -z "$line" ]]; then
                continue
            fi
            # Use eval to handle potential quotes, but simple export is safer for now
            # Assume key=value format
            if [[ "$line" =~ = ]]; then
                # Split key and value
                key=$(echo "$line" | cut -d '=' -f 1)
                value=$(echo "$line" | cut -d '=' -f 2-)
                # Export (remove surrounding quotes if present)
                value=${value%\"}
                value=${value#\"}
                value=${value%\'}
                value=${value#\'}
                export "$key=$value"
            fi
        done < "$env_file"
    fi
}

# Root .env 파일 로드
load_env ".env"

# Market Data .env 파일 로드
load_env "services/market-data/.env"

# 로컬 실행을 위한 환경변수 오버라이드
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
check_connection "localhost" "6379" "Redis"

# Move to the market-data service directory
cd "$(dirname "$0")/services/market-data"
export PYTHONPATH=src
# Run the loader using uv, passing all arguments
uv run -m quote_pipeline.loader.redis_asset_loader "$@"

