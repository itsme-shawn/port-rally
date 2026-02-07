# AI Advisor Service

포트폴리오 및 자산 분석을 위한 AI 서비스

## 기술 스택

- **Python 3.12+**
- **FastAPI**: RESTful API 프레임워크
- **LangChain**: LLM 오케스트레이션
- **Gemini 1.5 Flash**: Google의 저비용 LLM (월 $10 예산)
- **AsyncPG**: PostgreSQL 비동기 클라이언트
- **Redis**: 작업 큐 및 캐싱

## 설치

```bash
# uv로 의존성 설치
cd services/ai-advisor
uv sync

# 환경변수 설정
cp .env.example .env
# .env 파일에서 GOOGLE_API_KEY 등 설정
```

## 실행

```bash
# 개발 모드 (hot reload)
uv run python -m advisor.main

# 또는
uv run uvicorn advisor.main:app --reload --port 8081
```

## API 문서

서비스 실행 후 http://localhost:8081/docs에서 Swagger UI 확인

## 주요 엔드포인트

- `POST /v1/analyze/portfolio/{portfolio_id}` - 포트폴리오 분석 요청
- `GET /health` - 헬스 체크

## 비용 관리

- **모델**: Gemini 1.5 Flash (최저가)
- **분석 1건당 비용**: ~$0.00135
- **월 예산**: $10
- **월 분석 가능 건수**: ~7,400건
- **사용자 제한**: 월 10-20회/사용자

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `GOOGLE_API_KEY` | Gemini API 키 | - |
| `DATABASE_URL` | PostgreSQL 연결 URL | - |
| `REDIS_URL` | Redis 연결 URL | redis://localhost:6379/0 |
| `PORT` | 서비스 포트 | 8081 |
| `GEMINI_MODEL` | Gemini 모델명 | gemini-1.5-flash |
| `MAX_ANALYSES_PER_USER_PER_MONTH` | 사용자당 월 분석 제한 | 10 |
| `CACHE_TTL_HOURS` | 캐시 유효 시간 | 24 |

## 개발

```bash
# 테스트 실행
uv run pytest

# 코드 포맷팅
uv run ruff format .

# 린트
uv run ruff check .
```

## 배포

```bash
# Docker 빌드
docker build -t ai-advisor:latest .

# Docker 실행
docker run -p 8081:8081 --env-file .env ai-advisor:latest
```
