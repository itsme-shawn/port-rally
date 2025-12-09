# port-rally
PortRally : AI-powered real-time portfolio insights for smarter investment decisions.

## 1) 로컬 최초 세팅
```bash
# 필수 도구: docker, docker-compose (또는 docker compose), python3.12 (권장), uv

# 시세 모듈만 로컬에서 실행하려면

# (0) uv 미설치 된 경우 uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
# (1) Python 3.12 설치 (pyenv 역할)
uv python install 3.12
# (2) Python 3.12를 사용해 가상환경 생성 (venv 역할)
cd services/market-data
uv venv --python 3.12 # 현재 디렉토리 기준으로 .venv/ vhfej todtjd
# (3) 가상환경 활성화
source .venv/bin/activate
# (4) 패키지 설치 또는 동기화
uv sync            # pyproject.toml + uv.lock 기준으로 설치
# (5) python 모듈 검색 경로 지정
export PYTHONPATH=src
```

## 2) Docker Compose로 인프라 + 시세 모듈 구동
루트에 `.env`가 포함되어 있습니다(기본: Upbit, KRW-BTC/KRW-ETH, Redis 내부 호스트).
```bash
# 로컬 개발 (override 적용: 포트 노출/볼륨 마운트)
docker compose up -d

# 포트 바인딩 없이 내부 네트워크만
docker compose -f docker-compose.yml up -d

# 특정 컨테이너 제거 후 재생성
docker compose up --build --force-recreate <서비스명>
ex) docker compose up --build --force-recreate redis market-data
```
포트:
- Redis: 6379 (override 적용 시)
- Postgres: 5432:5432
- TimescaleDB: 5433→5432(내부)
- Kafka: 29092 (호스트), 9092 (내부)
- API: 8080:8080
- market-data: 내부 전용(포트 노출 없음)

### 컨테이너 재시작 요령
- Spring Boot(API) 코드만 바뀐 경우: 이미 `build`된 이미지가 있다면 `docker-compose up -d --build api`로 api 서비스만 재빌드·재시작.
- 모든 스택 초기화가 필요할 때: `docker-compose down` 후 `docker-compose up -d` (데이터는 볼륨 유지 시 남아있음).

### 컨테이너 관리/모니터링 기본 명령어
- 상태 보기: `docker-compose ps`
- 로그 실시간 보기: `docker-compose logs -f <service>` (예: `market-data`, `api`, `redis`)
- 특정 서비스 재시작: `docker-compose restart <service>`
- 특정 서비스 중지: `docker-compose stop <service>`
- 특정 서비스 다시 올리기(재빌드 포함): `docker-compose up -d --build <service>`
- 전체 중지/삭제: `docker-compose down` (볼륨 유지), `docker-compose down -v` (볼륨 삭제 주의)

### Redis 수신 확인 (컨테이너 기동 후)
1) Redis 구독
```bash
# 포트 노출 시 (override 적용)
redis-cli -u redis://localhost:6379/0 SUBSCRIBE quotes

# 포트 노출 안 했다면 컨테이너 내부에서
docker-compose exec redis redis-cli SUBSCRIBE quotes
```
2) 시세 메시지 수신 확인  
`market-data` 컨테이너가 `.env` 설정(PROVIDER/SYMBOLS 등)으로 실행 중이므로, 구독 창에 `message`, `quotes`, JSON 페이로드가 표시되면 정상 동작입니다.

## 3) 시세 모듈(quote_pipeline)과 로컬 Redis 연동 테스트

1) 터미널 A : 시세 데이터 pub
```bash
cd services/market-data
uv sync
source .venv/bin/activate
export PYTHONPATH=src

# Upbit → Redis Pub/Sub
uv run -m quote_pipeline.main \
  --provider upbit \
  --symbols KRW-BTC,KRW-ETH \
  --redis-url redis://localhost:6379/0 \
  --redis-channel quotes

# Binance 예시
uv run -m quote_pipeline.main \
  --provider binance \
  --symbols btcusdt,ethusdt \
  --channel trade \
  --redis-url redis://localhost:6379/0 \
  --redis-channel quotes
```

2) 터미널 B : 시세 데이터 sub

```bash
redis-cli -u redis://localhost:6379/0 SUBSCRIBE quotes
```
터미널 A에서 위 파이프라인 실행 후, 터미널 B에 `message`, `quotes`, JSON 페이로드가 보이면 연동 성공.
