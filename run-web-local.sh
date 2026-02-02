#!/bin/bash
# 로컬 Web 실행 스크립트
# Root .env.local을 로드하여 Next.js 실행

cd "$(dirname "$0")"

# Root .env 파일 로드
if [ -f ".env.local" ]; then
    # 주석 및 빈 줄 제거 후 export
    export $(cat .env.local | grep -v '^#' | grep -v '^$' | xargs)
    echo "✅ Loaded .env.local from root"
else
    echo "⚠️  Warning: .env.local file not found in root"
fi

cd apps/web

npm install

echo "🚀 Starting Next.js (Web)..."
npm run dev
