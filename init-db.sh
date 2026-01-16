#!/bin/bash

# .env 파일 로드 (환경 변수 설정)
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env"
fi

# 기본값 설정 (application.yml 기준)
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-portrally}
DB_HOST=${DB_HOST:-localhost}

echo "=========================================="
echo "   🚀 Database Init/Reset Script"
echo "=========================================="
echo "Target Database: $DB_NAME"
echo "Target User: $DB_USER"

# 실행 중인 Postgres 컨테이너 ID 찾기
CONTAINER_ID=$(docker compose ps -q postgres)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Postgres container is not running."
    echo "👉 Please start it with 'docker compose up -d postgres'."
    exit 1
fi

echo "Found Postgres container: $CONTAINER_ID"
echo "⚠️  WARNING: This will DROP ALL TABLES and DATA!"
echo "Are you sure you want to continue? (y/N)"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "🔄 Resetting database schema..."

# psql을 사용하여 public 스키마를 삭제하고 재생성
docker exec -i "$CONTAINER_ID" psql -U "$DB_USER" -d "$DB_NAME" <<EOSQL
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
GRANT ALL ON SCHEMA public TO "$DB_USER";
EOSQL

if [ $? -eq 0 ]; then
    echo "✅ Database initialized/reset successfully!"
    echo "👉 Restart your 'core-api' to apply the latest 'V*__schema_*.sql' files."
else
    echo "❌ Failed to initialize database."
    exit 1
fi
