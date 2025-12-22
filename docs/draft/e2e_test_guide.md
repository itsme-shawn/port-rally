# market-data 전체 테스트

## postgres, redis 는 한 번 띄우고 유지 (띄워져있으면 안 해도 됨)

docker compose up -d postgres
docker compose up -d redis

## market-data

docker compose run --rm --build market-data
(개발분 변경 있으면 --build 해야함)

## kis 모듈에서 단위테스트

uv run -m quote_pipeline.clients.kis.kis_main ws
(docker 를 띄운 상황에서는 APP key 중복 이슈 발생)

## redis 시세 sub
docker compose exec redis redis-cli SUBSCRIBE quotes

## redis 접속
docker compose exec redis redis-cli

## client 별 active_symbols 조회
SMEMBERS active_symbols:kis
SMEMBERS active_symbols:upbit
SMEMBERS active_symbols:binance

## 추가 (SADD)
SADD active_symbols:kis 005930 000660

## 삭제 (SREM)
SREM active_symbols:kis 005930

## 전체 삭제 (DEL)
DEL active_symbols
DEL active_symbols:kis

# redis 현재가 조회

KEYS "quote:*"

## 특정 quote Hash 내용 조회
HGETALL quote:US:NAS:NVDA
HGETALL quote:KR:UPBIT:KRW-BTC
HGETALL quote:CRYPTO:BINANCE:BTCUSDT

## quote 키 개수 확인
KEYS "quote:*" | wc -l

## 패턴별 조회
KEYS "quote:US:*"      # 미국 주식만
KEYS "quote:KR:*"      # 한국 주식/암호화폐만
KEYS "quote:CRYPTO:*"  # 바이낸스만
Docker 환경에서:
docker exec -it port-rally-redis-1 redis-cli KEYS "quote:*"
docker exec -it port-rally-redis-1 redis-cli HGETALL quote:US:NAS:NVDA


# 운영용 유틸

## 대화형 모드 (기본)
python -m quote_pipeline.manage

## Redis URL 지정
python -m quote_pipeline.manage --redis-url redis://localhost:6379

## Docker 환경
docker compose exec market-data python -m quote_pipeline.manage


# 기존 CLI 방식

## 기존 명령어 방식도 그대로 사용 가능
python -m quote_pipeline.manage symbols list kis
python -m quote_pipeline.manage quotes get NVDA

# 마스터 로더
의존 서비스 먼저 띄우기
docker compose up -d postgres redis
마스터 로더 1회 실행
docker compose run --rm --build market-data \
  uv run -m quote_pipeline.master_loader.master_loader
상시 실행(기본 main)

docker compose up -d market-data
이미 실행 중인 컨테이너에서 명령만 수행하려면

docker compose exec market-data \
  uv run -m quote_pipeline.master_loader.master_loa


## 로컬 실행
export PYTHONPATH=src
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME=port_rally
export REDIS_URL=redis://localhost:6379/0

uv run -m quote_pipeline.master_loader.master_loader




# docker 명령어

# 컨테이너

## 중지된(Exited) 컨테이너 삭제
docker container prune

## 특정 컨테이너만 삭제
docker rm container_id
또는 이름으로
docker rm port-rally_market-data_2

# 이미지

# 이미지 조회
docker images

## 안 쓰는 이미지 삭제 (참고로 이미지는 build 를 할 때 생긴다)
- 여러 번 build 를 하게 되면 기존 이미지는 옛 버전이 되면서 none 으로 돼서 쓰레기 이미지가 된다
docker image prune