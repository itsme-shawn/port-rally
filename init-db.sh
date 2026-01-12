#!/bin/bash

# .env 파일 로드 (환경 변수 설정)
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo "Loaded environment variables from .env"
fi

# 기본값 설정 (환경 변수가 없을 경우)
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-port_rally}

echo "Target Database: $DB_NAME"
echo "Target User: $DB_USER"

# 실행 중인 Postgres 컨테이너 ID 찾기
CONTAINER_ID=$(docker compose ps -q postgres)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Postgres container is not running. Please start it with 'docker compose up -d postgres'."
    exit 1
fi

echo "Found Postgres container: $CONTAINER_ID"
echo "Resetting database schema..."

# psql을 사용하여 public 스키마를 삭제하고 재생성
docker exec -i "$CONTAINER_ID" psql -U "$DB_USER" -d "$DB_NAME" <<EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
GRANT ALL ON SCHEMA public TO "$DB_USER";
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database schema initialized successfully!"
    echo "👉 You must restart your 'core-api' application to apply Flyway migrations."
else
    echo "❌ Failed to initialize database."
    exit 1
fi
