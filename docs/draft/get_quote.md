# Redis 시세 캐시 가이드 (PortRally)

## 📋 개요

PortRally의 실시간 시세 데이터는 Redis Hash 구조로 저장됩니다.
MVP 단계에서는 **현재가(price)** 정보만 저장합니다.

---

## 🔑 Key 구조

```
quote:{national}:{market}:{symbol}
```

### Key 구성 요소

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `national` | 국가/권역 코드 | `KR`, `US`, `HK`, `JP` |
| `market` | 거래소/마켓 코드 | `KOSPI`, `KOSDAQ`, `NAS`, `NYS` |
| `symbol` | 거래소 내 심볼 | `005930` (삼성전자), `AAPL` (애플) |

### Key 예시

```redis
quote:KR:KOSPI:005930      # 한국 KOSPI - 삼성전자
quote:KR:KOSDAQ:035720     # 한국 KOSDAQ - 카카오
quote:US:NAS:AAPL          # 미국 NASDAQ - 애플
quote:US:NYS:TSLA          # 미국 NYSE - 테슬라
```

---

## 📦 Value 구조 (Hash)

### MVP 필드 (현재)

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `price` | float | 현재가 | `71000` |

### 향후 확장 예정 필드 (Phase 2+)

```redis
# Phase 2에서 추가될 필드들 (참고용)
change          # 전일 대비 변동 금액
change_rate     # 전일 대비 변동률 (%)
volume          # 거래량
high            # 당일 고가
low             # 당일 저가
open            # 시가
prev_close      # 전일 종가
timestamp       # 업데이트 시각 (Unix timestamp)
```

---

## 🔧 Redis 명령어 예시

### 1. 시세 저장 (HSET)

```bash
# 기본 문법
HSET quote:{national}:{market}:{symbol} price {가격}

# 예시: 삼성전자 현재가 71,000원 저장
HSET quote:KR:KOSPI:005930 price 71000

# 예시: 애플 현재가 $185.50 저장
HSET quote:US:NAS:AAPL price 185.50
```

### 2. 시세 조회 (HGET)

```bash
# 기본 문법
HGET quote:{national}:{market}:{symbol} price

# 예시: 삼성전자 현재가 조회
HGET quote:KR:KOSPI:005930 price
# 반환: "71000"

# 예시: 애플 현재가 조회
HGET quote:US:NAS:AAPL price
# 반환: "185.50"
```

### 3. 전체 데이터 조회 (HGETALL)

```bash
# 기본 문법
HGETALL quote:{national}:{market}:{symbol}

# 예시: 삼성전자 전체 데이터 조회
HGETALL quote:KR:KOSPI:005930
# 반환: 
# 1) "price"
# 2) "71000"
```

### 4. 시세 존재 여부 확인 (EXISTS)

```bash
# 기본 문법
EXISTS quote:{national}:{market}:{symbol}

# 예시
EXISTS quote:KR:KOSPI:005930
# 반환: 1 (존재) 또는 0 (없음)
```

### 5. 시세 삭제 (DEL)

```bash
# 기본 문법
DEL quote:{national}:{market}:{symbol}

# 예시
DEL quote:KR:KOSPI:005930
```

---

## 💻 프로그래밍 언어별 예시

### Python (redis-py)

```python
import redis

# Redis 연결
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 1. 시세 저장
def save_quote(national, market, symbol, price):
    key = f"quote:{national}:{market}:{symbol}"
    r.hset(key, 'price', price)
    print(f"Saved: {key} = {price}")

# 2. 시세 조회
def get_quote(national, market, symbol):
    key = f"quote:{national}:{market}:{symbol}"
    price = r.hget(key, 'price')
    return float(price) if price else None

# 3. 여러 종목 일괄 조회 (Pipeline 사용)
def get_quotes_batch(securities):
    """
    securities: [(national, market, symbol), ...]
    예: [('KR', 'KOSPI', '005930'), ('US', 'NAS', 'AAPL')]
    """
    pipe = r.pipeline()
    
    for national, market, symbol in securities:
        key = f"quote:{national}:{market}:{symbol}"
        pipe.hget(key, 'price')
    
    results = pipe.execute()
    
    return {
        f"{nat}:{mkt}:{sym}": float(price) if price else None
        for (nat, mkt, sym), price in zip(securities, results)
    }

# 사용 예시
save_quote('KR', 'KOSPI', '005930', 71000)
save_quote('US', 'NAS', 'AAPL', 185.50)

price = get_quote('KR', 'KOSPI', '005930')
print(f"삼성전자 현재가: {price:,.0f}원")

quotes = get_quotes_batch([
    ('KR', 'KOSPI', '005930'),
    ('US', 'NAS', 'AAPL')
])
print(quotes)
# 출력: {'KR:KOSPI:005930': 71000.0, 'US:NAS:AAPL': 185.5}
```

### Node.js (ioredis)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

// 1. 시세 저장
async function saveQuote(national, market, symbol, price) {
    const key = `quote:${national}:${market}:${symbol}`;
    await redis.hset(key, 'price', price);
    console.log(`Saved: ${key} = ${price}`);
}

// 2. 시세 조회
async function getQuote(national, market, symbol) {
    const key = `quote:${national}:${market}:${symbol}`;
    const price = await redis.hget(key, 'price');
    return price ? parseFloat(price) : null;
}

// 3. 여러 종목 일괄 조회 (Pipeline 사용)
async function getQuotesBatch(securities) {
    const pipeline = redis.pipeline();
    
    securities.forEach(([national, market, symbol]) => {
        const key = `quote:${national}:${market}:${symbol}`;
        pipeline.hget(key, 'price');
    });
    
    const results = await pipeline.exec();
    
    const quotes = {};
    securities.forEach(([national, market, symbol], i) => {
        const price = results[i][1];
        quotes[`${national}:${market}:${symbol}`] = price ? parseFloat(price) : null;
    });
    
    return quotes;
}

// 사용 예시
await saveQuote('KR', 'KOSPI', '005930', 71000);
await saveQuote('US', 'NAS', 'AAPL', 185.50);

const price = await getQuote('KR', 'KOSPI', '005930');
console.log(`삼성전자 현재가: ${price.toLocaleString()}원`);

const quotes = await getQuotesBatch([
    ['KR', 'KOSPI', '005930'],
    ['US', 'NAS', 'AAPL']
]);
console.log(quotes);
```

### Go (go-redis)

```go
package main

import (
    "context"
    "fmt"
    "strconv"
    "github.com/go-redis/redis/v8"
)

var ctx = context.Background()

// 1. 시세 저장
func saveQuote(rdb *redis.Client, national, market, symbol string, price float64) error {
    key := fmt.Sprintf("quote:%s:%s:%s", national, market, symbol)
    return rdb.HSet(ctx, key, "price", price).Err()
}

// 2. 시세 조회
func getQuote(rdb *redis.Client, national, market, symbol string) (float64, error) {
    key := fmt.Sprintf("quote:%s:%s:%s", national, market, symbol)
    val, err := rdb.HGet(ctx, key, "price").Result()
    if err != nil {
        return 0, err
    }
    return strconv.ParseFloat(val, 64)
}

// 3. 여러 종목 일괄 조회
func getQuotesBatch(rdb *redis.Client, securities [][3]string) (map[string]float64, error) {
    pipe := rdb.Pipeline()
    
    cmds := make([]*redis.StringCmd, len(securities))
    for i, sec := range securities {
        key := fmt.Sprintf("quote:%s:%s:%s", sec[0], sec[1], sec[2])
        cmds[i] = pipe.HGet(ctx, key, "price")
    }
    
    _, err := pipe.Exec(ctx)
    if err != nil && err != redis.Nil {
        return nil, err
    }
    
    quotes := make(map[string]float64)
    for i, cmd := range cmds {
        sec := securities[i]
        key := fmt.Sprintf("%s:%s:%s", sec[0], sec[1], sec[2])
        
        val, err := cmd.Result()
        if err == nil {
            price, _ := strconv.ParseFloat(val, 64)
            quotes[key] = price
        }
    }
    
    return quotes, nil
}

// 사용 예시
func main() {
    rdb := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
    })
    
    // 저장
    saveQuote(rdb, "KR", "KOSPI", "005930", 71000)
    saveQuote(rdb, "US", "NAS", "AAPL", 185.50)
    
    // 조회
    price, _ := getQuote(rdb, "KR", "KOSPI", "005930")
    fmt.Printf("삼성전자 현재가: %.0f원\n", price)
    
    // 일괄 조회
    securities := [][3]string{
        {"KR", "KOSPI", "005930"},
        {"US", "NAS", "AAPL"},
    }
    quotes, _ := getQuotesBatch(rdb, securities)
    fmt.Println(quotes)
}
```

---

## 🗃️ PostgreSQL 종목 정보와 연동

Redis의 시세 데이터는 PostgreSQL의 `securities_master` 테이블과 연동됩니다.

### PostgreSQL 테이블 구조 (참고)

```sql
CREATE TABLE securities_master (
    security_id BIGSERIAL PRIMARY KEY,
    national VARCHAR(10) NOT NULL,      -- Redis의 {national}
    market VARCHAR(20) NOT NULL,        -- Redis의 {market}
    symbol VARCHAR(20) NOT NULL,        -- Redis의 {symbol}
    name_ko VARCHAR(200),
    name_en VARCHAR(200),
    asset_type VARCHAR(20),
    currency VARCHAR(3) NOT NULL,
    
    CONSTRAINT uq_security UNIQUE(national, market, symbol)
);
```

### 연동 플로우

```

1. redis 의 active_symbols 에 종목 변경 이벤트 발생
1. PostgreSQL에서 해당 종목 조회
2. (national, market, symbol) 추출
3. Redis에서 시세 조회: quote:{national}:{market}:{symbol}
4. 결과 병합 후 사용자에게 반환
```

### 연동 예시 (Python)

```python
import psycopg2
import redis

# DB 연결
pg = psycopg2.connect(
    host="localhost",
    database="portrally",
    user="postgres",
    password="password"
)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_security_with_price(security_id):
    """종목 정보 + 현재가 조회"""
    
    # 1. PostgreSQL에서 종목 정보 조회
    cur = pg.cursor()
    cur.execute("""
        SELECT security_id, national, market, symbol, name_ko, name_en, currency
        FROM securities_master
        WHERE security_id = %s
    """, (security_id,))
    
    row = cur.fetchone()
    if not row:
        return None
    
    security = {
        'security_id': row[0],
        'national': row[1],
        'market': row[2],
        'symbol': row[3],
        'name_ko': row[4],
        'name_en': row[5],
        'currency': row[6],
    }
    
    # 2. Redis에서 현재가 조회
    key = f"quote:{security['national']}:{security['market']}:{security['symbol']}"
    price = r.hget(key, 'price')
    
    security['price'] = float(price) if price else None
    
    return security

# 사용 예시
result = get_security_with_price(1)
print(result)
# {
#     'security_id': 1,
#     'national': 'KR',
#     'market': 'KOSPI',
#     'symbol': '005930',
#     'name_ko': '삼성전자',
#     'name_en': 'Samsung Electronics',
#     'currency': 'KRW',
#     'price': 71000.0
# }
```

---

## ⚡ 성능 최적화 팁

### 1. Pipeline 사용 (필수)

여러 종목을 조회할 때는 반드시 Pipeline을 사용하세요.

```python
# ❌ 나쁜 예: 루프에서 개별 조회 (RTT x N)
for symbol in ['005930', '000660', '035720']:
    price = r.hget(f'quote:KR:KOSPI:{symbol}', 'price')

# ✅ 좋은 예: Pipeline 사용 (RTT x 1)
pipe = r.pipeline()
for symbol in ['005930', '000660', '035720']:
    pipe.hget(f'quote:KR:KOSPI:{symbol}', 'price')
results = pipe.execute()
```

### 2. Connection Pool 사용

```python
import redis

# ✅ Connection Pool 사용
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True
)
r = redis.Redis(connection_pool=pool)
```

### 3. 캐싱 전략

```python
# 프론트엔드에서 자주 요청하는 종목은 메모리 캐싱
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_quote_cached(national, market, symbol, ttl_seconds=1):
    """1초간 캐싱 (실시간성과 성능의 균형)"""
    key = f"quote:{national}:{market}:{symbol}"
    return r.hget(key, 'price')
```

---

## 🚨 주의사항

### 1. Key 네이밍 규칙

- ✅ 소문자 사용: `quote:kr:kospi:005930` (권장)
- ⚠️ 대문자 허용: `quote:KR:KOSPI:005930` (가독성 우선 시)
- ❌ 공백 금지: `quote:KR KOSPI 005930`
- ❌ 특수문자 금지: `quote:KR/KOSPI/005930`

### 2. 타입 변환

Redis는 모든 값을 문자열로 저장합니다.

```python
# 저장
r.hset('quote:KR:KOSPI:005930', 'price', 71000)

# 조회 (문자열로 반환됨)
price = r.hget('quote:KR:KOSPI:005930', 'price')
# price = "71000" (문자열)

# ✅ 반드시 숫자로 변환
price = float(price)  # 71000.0 (숫자)
```

### 3. None 처리

종목이 Redis에 없을 수 있습니다.

```python
price = r.hget('quote:KR:KOSPI:999999', 'price')
# price = None

# ✅ None 체크 필수
if price is not None:
    price = float(price)
else:
    price = 0.0  # 또는 에러 처리
```

### 4. TTL 관리 (나중에 추가 예정)

```redis
# Phase 2에서 TTL 추가 예정
EXPIRE quote:KR:KOSPI:005930 3600  # 1시간 후 자동 삭제
```

---

## 📊 데이터 예시

### 한국 종목 (KRW)

```redis
# 삼성전자
HSET quote:KR:KOSPI:005930 price 71000

# SK하이닉스
HSET quote:KR:KOSPI:000660 price 142000

# 카카오
HSET quote:KR:KOSDAQ:035720 price 45500
```

### 미국 종목 (USD)

```redis
# 애플
HSET quote:US:NAS:AAPL price 185.50

# 테슬라
HSET quote:US:NAS:TSLA price 242.84

# Microsoft
HSET quote:US:NAS:MSFT price 378.91
```

---

## 🔍 디버깅 명령어

```bash
# 1. 모든 시세 key 확인
KEYS quote:*

# 2. 특정 종목 데이터 확인
HGETALL quote:KR:KOSPI:005930

# 3. 전체 Hash 필드 개수
HLEN quote:KR:KOSPI:005930

# 4. Redis 메모리 사용량 확인
INFO memory

# 5. 특정 key 메모리 사용량
MEMORY USAGE quote:KR:KOSPI:005930
```

---

## 📝 체크리스트

Agent 구현 전 확인사항:

- [ ] Redis 연결 테스트 완료
- [ ] Key 네이밍 규칙 이해 (`quote:{national}:{market}:{symbol}`)
- [ ] HGET/HSET 명령어 사용법 숙지
- [ ] Pipeline 사용법 이해 (다중 조회 시 필수)
- [ ] 문자열 → 숫자 변환 로직 추가
- [ ] None 체크 로직 추가
- [ ] PostgreSQL 연동 방법 이해

---

## 🆘 문제 해결

### Q1. Redis에 시세가 없어요

```python
# 확인 1: Key가 정확한가?
r.exists('quote:KR:KOSPI:005930')  # 1이면 존재, 0이면 없음

# 확인 2: PostgreSQL에 종목이 있나?
SELECT * FROM securities_master 
WHERE national='KR' AND market='KOSPI' AND symbol='005930';

# 해결: 시세 파이프라인이 동작 중인지 확인
```

### Q2. 가격이 문자열로 나와요

```python
# ❌ 잘못된 코드
price = r.hget('quote:KR:KOSPI:005930', 'price')
print(price + 1000)  # ERROR: str + int

# ✅ 올바른 코드
price = r.hget('quote:KR:KOSPI:005930', 'price')
if price:
    price = float(price)
    print(price + 1000)
```

### Q3. 성능이 느려요

```python
# ❌ 100개 종목을 개별 조회 (느림)
for symbol in symbols:
    price = r.hget(f'quote:KR:KOSPI:{symbol}', 'price')

# ✅ Pipeline 사용 (빠름)
pipe = r.pipeline()
for symbol in symbols:
    pipe.hget(f'quote:KR:KOSPI:{symbol}', 'price')
results = pipe.execute()
```