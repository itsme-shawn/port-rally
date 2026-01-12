#!/bin/bash
set -e

# .env 파일 로드
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env"
fi

# 로컬 실행 시 DB_HOST는 localhost여야 함 (Docker 외부에서 실행하므로)
export DB_HOST=localhost

# market-data 서비스 디렉토리로 이동
cd "$(dirname "$0")/services/market-data"

echo "Starting Master Loader (Target DB: $DB_HOST)..."

# PYTHONPATH 설정 및 실행
if command -v uv &> /dev/null; then
    PYTHONPATH=src uv run src/quote_pipeline/master_loader/master_loader.py
else
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    python3 src/quote_pipeline/master_loader/master_loader.py
fi

echo "✅ Master Loader completed successfully!"
