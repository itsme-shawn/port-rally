#!/bin/bash

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

check_connection "localhost" "6379" "Redis"

# Move to the market-data service directory
cd "$(dirname "$0")/services/market-data"
export PYTHONPATH=src

# Check if the first argument is a number (for convenience)
if [[ "$1" =~ ^[0-9]+$ ]]; then
    COUNT=$1
    shift # Remove the number from arguments
    echo "Running benchmark with count: $COUNT"
    uv run -m quote_pipeline.benchmark.redis_search_bench --count "$COUNT" "$@"
else
    # Run the benchmark passing all arguments directly
    uv run -m quote_pipeline.benchmark.redis_search_bench "$@"
fi
