# AI Advisor 서비스 다음 단계

## 1. 환경 설정 및 테스트 (30분)

```bash
cd services/ai-advisor

# 1. 의존성 설치
uv sync

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 수정:
# - GOOGLE_API_KEY=your_gemini_api_key
# - DATABASE_URL=postgresql://portrally:password@localhost:5432/portrally
# - REDIS_URL=redis://localhost:6379/0

# 3. 서비스 실행
uv run python -m advisor.main

# 4. API 테스트 (다른 터미널)
curl http://localhost:8081/health
curl -X POST http://localhost:8081/v1/analyze/portfolio/{portfolio_id}
```

## 2. Core-API 통합 (1-2일)

### 2.1 Java 코드 추가

```java
// apps/core-api/src/main/java/api/controller/PortfolioInsightController.java
@RestController
@RequestMapping("/api/v1/portfolios/{portfolioId}/insights")
public class PortfolioInsightController {
    // TODO: 구현
}

// apps/core-api/src/main/java/api/service/insight/PortfolioInsightService.java
@Service
public class PortfolioInsightService {
    // TODO: 구현
}
```

### 2.2 DB 마이그레이션

```sql
-- apps/core-api/src/main/resources/db/migration/V7__add_user_analysis_usage.sql
CREATE TABLE user_analysis_usage (
    user_id UUID REFERENCES users(user_id),
    year_month VARCHAR(7) NOT NULL,
    analysis_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, year_month)
);
```

## 3. 프론트엔드 UI (2-3일)

```typescript
// apps/web/app/(main)/portfolio/insights/page.tsx
export default function PortfolioInsightsPage() {
  // 분석 요청 버튼
  // 진행 상태 표시
  // 결과 표시 (건강도 점수, 리포트)
}
```

## 4. Redis 작업 큐 구현 (선택사항)

현재는 FastAPI BackgroundTasks 사용 중.
더 견고한 처리를 위해 Redis 큐 추가 가능:

```python
# src/advisor/workers/job_consumer.py
async def consume_redis_queue():
    # Redis BRPOP으로 작업 소비
    # 포트폴리오 분석 실행
    # 상태 업데이트
```

## 5. 모니터링 및 로깅

- [ ] Prometheus metrics 추가
- [ ] Sentry 에러 트래킹
- [ ] 비용 추적 대시보드

## 6. Phase 2: 자산 분석

- [ ] 자산 분석 엔드포인트 추가
- [ ] 뉴스 감성 분석 체인
- [ ] AssetInsightService 구현

## 우선순위 작업

1. ✅ Gemini API 키 발급 (https://aistudio.google.com/)
2. ✅ 서비스 로컬 실행 및 테스트
3. ⏳ Core-API 통합 (PortfolioInsightController)
4. ⏳ 프론트엔드 UI
5. ⏳ 배포 (Docker Compose)

## 비용 모니터링

매일 확인:
```bash
# Gemini API 사용량 확인
# Google Cloud Console > APIs & Services > Credentials
```

월말 예산 초과 방지:
- 사용자당 월 10회 제한
- 캐시 24시간 (중복 분석 방지)
- Rate limiting
