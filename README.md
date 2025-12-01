# port-rally
PortRally : AI-powered real-time portfolio insights for smarter investment decisions.

## 1) 로컬 최초 세팅
```bash
# 필수 도구: docker, docker-compose (또는 docker compose), python3

# (선택) Python venv for local runs
cd services/market-data
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

## 2) Docker Compose로 인프라 + 시세 모듈 구동
루트에 `.env`가 포함되어 있습니다(기본: Upbit, KRW-BTC/KRW-ETH, Redis 내부 호스트).
```bash
# 로컬 개발 (override 적용: 포트 노출/볼륨 마운트)
docker-compose up -d

# 포트 바인딩 없이 내부 네트워크만
docker-compose -f docker-compose.yml up -d
```
포트:
- Redis: 6379 (override 적용 시)
- market-data: 내부 전용(포트 노출 없음)

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

## 3) 시세 모듈(quote_pipeline) 단독 실행 예
```bash
cd services/market-data
source .venv/bin/activate
export PYTHONPATH=src

# Upbit → Redis Pub/Sub
python -m quote_pipeline.main \
  --provider upbit \
  --symbols KRW-BTC,KRW-ETH \
  --redis-url redis://localhost:6379/0 \
  --redis-channel quotes

# Binance 예시
python -m quote_pipeline.main \
  --provider binance \
  --symbols btcusdt,ethusdt \
  --channel trade \
  --redis-url redis://localhost:6379/0 \
  --redis-channel quotes
```

## 4) Redis Pub/Sub 수신 확인
터미널 A:
```bash
redis-cli -u redis://localhost:6379/0 SUBSCRIBE quotes
```
터미널 B에서 위 파이프라인 실행 후, 터미널 A에 `message`, `quotes`, JSON 페이로드가 보이면 정상 수신입니다.
