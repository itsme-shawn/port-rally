# Market Data Pipeline 아키텍처

> **최종 수정일**: 2026-01-04
> **관련 서비스**: services/market-data

---

## 목차

1. [개요](#1-개요)
2. [전체 아키텍처](#2-전체-아키텍처)
3. [레이어별 상세 설명](#3-레이어별-상세-설명)
4. [실행 모드](#4-실행-모드)
5. [데이터 흐름](#5-데이터-흐름)
6. [KIS Provider 상세](#6-kis-provider-상세)
7. [실행 가이드](#7-실행-가이드)
8. [리팩토링 히스토리](#8-리팩토링-히스토리)

---

## 1. 개요

### 1.1 목적

Market Data Pipeline은 여러 거래소(KIS, Upbit, Binance)의 실시간 시세 데이터를 수집하여 Redis에 저장하는 시스템이다

### 1.2 핵심 기능

- **다중 Provider 지원**: KIS(국내/해외 주식), Upbit(암호화폐), Binance(암호화폐)
- **동적 심볼 관리**: Redis Set을 통한 런타임 심볼 추가/제거
- **실시간 시세 발행**: Redis Pub/Sub 및 Hash 저장
- **재연결 및 복구**: WebSocket 연결 실패 시 자동 재연결

### 1.3 기술 스택

- **언어**: Python 3.12
- **프레임워크**: asyncio, websockets
- **데이터베이스**: PostgreSQL (종목 마스터)
- **캐시**: Redis (시세 저장, Pub/Sub, 동적 심볼 관리)

---

## 2. 전체 아키텍처

### 2.1 레이어 구조

```
┌─────────────────────────────────────────────────────────┐
│                    BaseIngestor                          │
│                 (Thin Orchestrator)                      │
└─────────────────────────────────────────────────────────┘
         │              │              │              │
         ↓              ↓              ↓              ↓
  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
  │  Client  │  │   Parser    │  │  Mapper  │  │Publisher │
  │ (입력포트) │  │  (파싱)     │  │  (변환)   │  │(출력포트) │
  └──────────┘  └─────────────┘  └──────────┘  └──────────┘
         │              │              │              │
         ↓              ↓              ↓              ↓
    WebSocket      DTO 추출    UniQuoteDto    Redis/Stdout
```

### 2.2 디렉토리 구조

```
quote_pipeline/
├── clients/                    # 외부 시스템 클라이언트 (입력 포트)
│   ├── base_client.py          # BaseClient (abstract)
│   ├── kis/
│   │   ├── kis_client.py       # KisClient (WebSocket lifecycle)
│   │   ├── kis_auth_client.py  # 인증 클라이언트
│   │   ├── kis_ws_client.py    # WebSocket 메시지 빌더
│   │   ├── kis_rest_client.py  # REST API 클라이언트
│   │   └── kis_config.py       # KIS 설정
│   ├── upbit/
│   │   └── upbit_client.py     # UpbitClient
│   └── binance/
│       └── binance_client.py   # BinanceClient
│
├── parsers/                    # 메시지 파싱 레이어
│   ├── message_parser.py       # MessageParser (abstract)
│   ├── kis_message_parser.py   # KIS 파서
│   ├── upbit_message_parser.py # Upbit 파서
│   └── binance_message_parser.py # Binance 파서
│
├── mappers/                    # DTO → Domain Event 변환
│   ├── base_mapper.py          # BaseMapper (abstract)
│   ├── kis_quote_mapper.py     # KIS 매퍼
│   ├── upbit_quote_mapper.py   # Upbit 매퍼
│   └── binance_quote_mapper.py # Binance 매퍼
│
├── domain/                     # 도메인 객체 (DTOs)
│   ├── uni_quote_dto.py        # 통합 시세 DTO
│   └── kis_*_dto.py            # Provider별 DTOs
│
├── services/                   # 재사용 가능한 비즈니스 로직
│   ├── symbol_service.py       # 심볼 관리 (캐싱, DB 조회)
│   └── subscription_service.py # 구독 상태 추적
│
├── publishers/                 # 출력 포트 (Sinks)
│   ├── base_publisher.py       # Publisher (abstract)
│   ├── redis_publisher.py      # RedisPublisher
│   └── stdout_publisher.py     # StdoutPublisher
│
├── ingestors/                  # 파이프라인 조립 및 실행
│   ├── base_ingestor.py        # BaseIngestor (orchestrator)
│   ├── ingestor_factory.py     # 팩토리 함수
│   └── ingestor_manager.py     # 4가지 실행 모드 관리
│
├── infrastructure/             # 인프라 레이어
│   ├── db.py                   # PostgreSQL 연결
│   ├── redis.py                # Redis 연결 풀
│   └── stores/
│       ├── quote_store.py      # Redis 시세 저장
│       └── active_symbols_store.py # 동적 심볼 관리
│
├── utils/                      # 유틸리티
│   └── trading_hours.py        # 거래 시간 체크
│
├── config.py                   # 설정 관리
├── main.py                     # CLI entry point
└── manage.py                   # 운영 유틸리티
```

---

## 3. 레이어별 상세 설명

### 3.1 Domain Layer

**기능**: 시스템의 핵심 도메인 객체 정의

#### UniQuoteDto (통합 시세 DTO)

```python
@dataclass
class UniQuoteDto:
    symbol: str              # 종목 코드
    national: str            # 국가 (KR, US, HK, etc.)
    market: str              # 시장 (KOSPI, NAS, NYS, etc.)
    price: Decimal           # 현재가
    timestamp: datetime      # 시각
```

### 3.2 Clients Layer

**기능**: 외부 시스템과의 통신 (WebSocket, REST API)

#### BaseClient (추상 클래스)

```python
class BaseClient(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """외부 시스템 연결"""

    @abstractmethod
    async def subscribe(self, symbols: Iterable[str]) -> None:
        """심볼 구독 등록"""

    @abstractmethod
    async def receive(self) -> str:
        """메시지 수신"""

    @abstractmethod
    async def close(self) -> None:
        """연결 종료"""
```

### 3.3 Parsers Layer

**기능**: raw 메시지 → DTO 변환

#### KisMessageParser

```python
class KisMessageParser(MessageParser):
    def parse(self, message: str) -> Union[
        KisOverseasQuoteDTO,
        KisDomesticQuoteDTO,
        KisSubscriptionResponseDTO
    ]:
        """KIS 메시지를 파싱하여 적절한 DTO 반환"""
        tr_id = self._detect_tr_id(message)

        if tr_id == "HDFSCNT0":
            return self._parse_overseas(message)
        elif tr_id == "H0UNCNT0":
            return self._parse_domestic(message)
        else:
            return self._parse_json(message)
```

### 3.4 Mappers Layer

**기능**: DTO → UniQuoteDto 변환 (정규화)

#### KisQuoteMapper

```python
class KisQuoteMapper(BaseMapper):
    def to_uni_quote(
        self,
        dto: Union[KisOverseasQuoteDTO, KisDomesticQuoteDTO]
    ) -> UniQuoteDto:
        """Provider별 DTO를 통합 시세 DTO로 변환"""

        if isinstance(dto, KisOverseasQuoteDTO):
            return self._map_overseas_quote(dto)
        else:
            return self._map_domestic_quote(dto)
```

### 3.5 Services Layer

**기능**: 재사용 가능한 비즈니스 로직

#### SymbolService

- **역할**: 심볼 → 마켓 정보 캐싱 및 조회
- **데이터 소스**: PostgreSQL `securities_master` 테이블
- **캐시 구조**: `{symbol: (market, national)}`

```python
# 예시
service.get_market_info("005930")  # ("KOSPI", "KR")
service.get_market_info("NVDA")    # ("NAS", "US")
```

#### SubscriptionService

- **역할**: 구독 상태 추적
- **메서드**:
  - `mark_subscribed()`: 구독 등록
  - `calculate_changes()`: 증분 구독 계산

### 3.6 Publishers Layer

**책임**: 도메인 이벤트를 외부로 발행

#### RedisPublisher

- **기능**: Redis Pub/Sub 및 Hash 저장
- **Key 구조**: `quote:{national}:{market}:{symbol}`

```bash
# 예시
HSET quote:KR:KOSPI:005930 price 71000
PUBLISH quotes {"symbol":"005930","price":71000,...}
```

---

## 4. 실행 모드

### 4.1 4가지 모드 조합

| 모드 | Provider 수 | 심볼 관리 | 설명 |
|------|-------------|-----------|------|
| `single_static` | 1개 | 고정 | 가장 기본적인 형태 |
| `single_dynamic` | 1개 | Redis 동적 | 단일 provider + 동적 심볼 |
| `multi_static` | 여러 개 | 고정 | 여러 provider 동시 실행 |
| `multi_dynamic` | 여러 개 | Redis 동적 | 여러 provider + 동적 심볼 (권장) |

### 4.2 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `PROVIDER` | 단일 provider | `kis_new` |
| `PROVIDERS` | 다중 provider (콤마 구분) | `kis_new,upbit,binance` |
| `SYMBOLS` | 심볼 목록 (콤마 구분) | `NVDA,KRW-BTC,btcusdt` |
| `DYNAMIC_ENABLED` | 동적 모드 활성화 | `true` |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379/0` |

### 4.3 실행 예시

#### single_static (단일 provider, 고정 심볼)

```bash
PROVIDER=kis_new SYMBOLS=NVDA,AAPL,005930 \
uv run python -m quote_pipeline.main
```

#### multi_dynamic (다중 provider, 동적 심볼) - 권장

```bash
PROVIDERS=kis_new,upbit,binance SYMBOLS=NVDA,KRW-BTC,btcusdt \
DYNAMIC_ENABLED=true \
REDIS_URL=redis://localhost:6379/0 \
uv run python -m quote_pipeline.main --dynamic
```

---

## 5. 데이터 흐름

### 5.1 정적 모드 (Static Symbol)

고정 심볼

```
1. 환경변수/CLI → Settings 객체
2. Settings → Publisher 생성 (Redis/Stdout)
3. Settings → BaseIngestor 생성
   ├── Client (WebSocket 연결)
   ├── Parser (메시지 파싱)
   ├── Mapper (DTO 변환)
   └── Services (심볼/구독 관리)
4. BaseIngestor.run_forever()
   ├── connect()
   ├── subscribe(symbols)
   └── while True:
       ├── receive() → raw message
       ├── parse() → DTO
       ├── map() → UniQuoteDto
       └── publish() → Redis
```

### 5.2 동적 모드 (Dynamic Symbol)

유동 심볼

```
1. Redis Set "active_symbols:{provider}" ← 초기 심볼 seed
2. IngestorManager.run_*_dynamic_symbol()
3. [폴링 루프 - 5초마다]
   Redis SMEMBERS "active_symbols:{provider}"
   → 심볼 변경 감지
   → BaseIngestor.apply_symbols(new_symbols)
   → Client.apply_symbols()
   → 증분 구독/해지
```

### 5.3 메시지 처리 파이프라인

```
WebSocket 메시지 수신
      ↓
BaseClient (외부 연결)
      ↓
MessageParser (raw → DTO)
      ↓
BaseMapper (DTO → UniQuoteDto)
      ↓
Publisher (외부 발행)
```

---

## 6. KIS Provider 상세

### 6.1 KIS Provider 아키텍처 개요

KIS Provider는 한국투자증권(KIS) OpenAPI의 WebSocket 실시간 시세를 수신하는 클라이언트이다. 다음 4개의 핵심 컴포넌트로 구성된다:

```
┌─────────────────────────────────────────────────────────────┐
│                        KisClient                             │
│                  (WebSocket 라이프사이클 관리)                 │
│                                                               │
│  - connect()      : WebSocket 연결 수립                        │
│  - subscribe()    : 심볼 구독 등록                             │
│  - receive()      : 메시지 수신                                │
│  - apply_symbols(): 동적 구독 변경                             │
│  - close()        : 연결 종료                                  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ↓                    ↓                    ↓
   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
   │  KisConfig   │   │KisWsAuthClient│   │  KisWsClient    │
   │   (설정)      │   │  (인증관리)    │   │(메시지 빌더)     │
   └──────────────┘   └──────────────┘   └──────────────────┘
```

**의존성**:
- **KisConfig**: API 키, URL 설정
- **KisWsAuthClient**: Approval Key 발급 및 캐싱
- **KisWsClient**: WebSocket 메시지 생성
- **SymbolService**: 심볼 메타데이터 조회 (national, exchange)
- **SubscriptionService**: 구독 상태 추적 및 증분 계산

---

### 6.2 KisConfig: 설정 관리

**파일**: [kis_config.py](../services/market-data/src/quote_pipeline/clients/kis/kis_config.py)

#### 6.2.1 설정 클래스

```python
@dataclass
class KisConfig:
    app_key: str          # API 키
    app_secret: str       # API 시크릿
    is_vts: bool = False  # 모의투자 여부

    @property
    def base_url(self) -> str:
        """REST API Base URL"""
        if self.is_vts:
            return "https://openapivts.koreainvestment.com:29443"
        return "https://openapi.koreainvestment.com:9443"

    @property
    def ws_base_url(self) -> str:
        """WebSocket Base URL (다중연결)"""
        if self.is_vts:
            return "ws://ops.koreainvestment.com:31000"  # 모의
        return "ws://ops.koreainvestment.com:21000"      # 실전
```

#### 6.2.2 TR_ID 상수

KIS WebSocket 요청 시 body에 들어갈 TR_ID 값

```python
class KisTrId(str, Enum):
    """KIS WebSocket TR_ID 상수"""
    DOMESTIC_TICK = "H0UNCNT0"  # 국내주식 실시간체결가(통합)
    OVERSEAS_TICK = "HDFSCNT0"  # 해외주식 실시간체결가
```

#### 6.2.3 TR_TYPE 상수

WebSocket 연결에서 특정 종목 구독 등록/해제

```python
class KisTrType(str, Enum):
    """KIS WebSocket 구독 타입"""
    REGISTER = "1"    # 등록
    UNREGISTER = "2"  # 해제
```

#### 6.2.4 KisSubscription: 구독 정보 생성

```python
@dataclass(frozen=True)
class KisSubscription:
    """KIS 구독 정보"""
    tr_id: str    # H0UNCNT0 또는 HDFSCNT0
    tr_key: str   # 구독 키 (국내: 심볼, 해외: D{exchange}{symbol})
    symbol: str   # 원본 심볼

    @classmethod
    def for_domestic(cls, symbol: str) -> "KisSubscription":
        """국내주식: tr_key = 심볼 그대로"""
        return cls(
            tr_id=KisTrId.DOMESTIC_TICK.value,
            tr_key=symbol,
            symbol=symbol,
        )

    @classmethod
    def for_overseas(cls, symbol: str, exchange: str) -> "KisSubscription":
        """해외주식: tr_key = D{exchange}{symbol}"""
        tr_key = f"D{exchange}{symbol}"
        return cls(
            tr_id=KisTrId.OVERSEAS_TICK.value,
            tr_key=tr_key,
            symbol=symbol,
        )
```

#### 6.2.5 build_subscription 헬퍼 함수

```python
def build_subscription(
    symbol: str,
    national: str,
    exchange: str | None = None
) -> KisSubscription:
    """
    심볼과 국가/거래소 정보로 구독 정보를 생성합니다.

    Args:
        symbol: 종목 코드
        national: 국가 코드 ("KR", "US", "HK" 등)
        exchange: 해외주식 거래소 코드 (NAS, NYS, AMS, HKS 등). 국내는 None.

    Returns:
        KisSubscription 인스턴스
    """
    if national == "KR":
        return KisSubscription.for_domestic(symbol)

    if exchange is None:
        raise ValueError(f"Exchange required for {symbol} (national={national})")

    return KisSubscription.for_overseas(symbol, exchange)
```

**TR_KEY 생성 예시**:

| 심볼 | National | Exchange | TR_ID | TR_KEY |
|------|----------|----------|-------|--------|
| 005930 | KR | - | H0UNCNT0 | `005930` |
| 196170 | KR | - | H0UNCNT0 | `196170` |
| NVDA | US | NAS | HDFSCNT0 | `DNASNVDA` |
| AA | US | NYS | HDFSCNT0 | `DNYSAA` |
| AAAU | US | AMS | HDFSCNT0 | `DAMSAAAU` |
| 5 | HK | HKS | HDFSCNT0 | `DHKS5` |

---

### 6.3 KisWsAuthClient: 인증 관리

**파일**: [kis_auth_client.py](../services/market-data/src/quote_pipeline/clients/kis/kis_auth_client.py)

KIS OpenAPI는 두 가지 인증 토큰을 사용합니다:
1. **Access Token**: REST API용 (`/oauth2/tokenP`)
2. **Approval Key**: WebSocket용 (`/oauth2/Approval`)

#### 6.3.1 KisRestAuthClient (REST 토큰)

```python
class KisRestAuthClient:
    """접근토큰(/oauth2/tokenP) 발급 및 캐시 관리"""

    def __init__(self, config: KisConfig, token_path: Optional[Path] = None):
        self.cfg = config
        self.token_path = token_path or Path("token_cache_rest.json")
        self._access: Optional[TokenResponse] = None
        self._expires_at: Optional[datetime] = None
        # 캐시에서 토큰 로드
        self._access, self._expires_at = load_token_from_file(self.token_path)

    def get_valid_access_token(self, buffer_sec: int = 60) -> str:
        """캐시된 토큰이 유효하면 재사용, 만료 임박 시 재발급"""
        if self._access and self._expires_at:
            if datetime.now(timezone.utc) + timedelta(seconds=buffer_sec) < self._expires_at:
                logger.info("Reusing cached access_token (expires_at=%s)", self._expires_at)
                return self._access.access_token

        logger.info("Cached token expiring soon. Requesting new token.")
        resp = self.issue_access_token()
        return resp.access_token

    def issue_access_token(self) -> TokenResponse:
        """POST /oauth2/tokenP"""
        url = f"{self.cfg.base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.cfg.app_key,
            "appsecret": self.cfg.app_secret,
        }
        resp = self.session.post(url, json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._access = TokenResponse.from_json(data)
        self._expires_at = self._parse_expiry(self._access)
        save_token_to_file(self.token_path, self._access, self._expires_at)
        return self._access
```

**캐시 파일 구조** (`token_cache_rest.json`):
```json
{
  "access": {
    "access_token": "eyJ0eXAiOiJKV1Q...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "access_token_token_expired": "2026-01-06 10:30:00"
  },
  "expires_at": "2026-01-06T10:30:00+00:00"
}
```

#### 6.3.2 KisWsAuthClient (WebSocket Approval Key)

```python
class KisWsAuthClient:
    """WebSocket Approval Key 발급/캐시 클라이언트"""

    def __init__(
        self,
        config: KisConfig,
        token_path: Optional[Path] = None,
        validity_seconds: int = 24 * 3600,  # 24시간
    ):
        self.cfg = config
        self.token_path = token_path or _get_token_cache_path("token_cache_ws.json")
        self.validity_seconds = validity_seconds
        self._approval: Optional[ApprovalResponse] = None
        self._expires_at: Optional[datetime] = None
        self._load_cache()

    def get_valid_approval_key(self, buffer_sec: int = 60) -> str:
        """캐시된 키가 유효하면 재사용, 만료 임박 시 재발급"""
        if self._approval and self._expires_at:
            now = datetime.now(timezone.utc)
            if now + timedelta(seconds=buffer_sec) < self._expires_at:
                logger.info("Reusing cached approval_key (expires_at=%s)", self._expires_at)
                return self._approval.approval_key

        logger.info("Cached approval_key expiring. Requesting new one.")
        return self.issue_approval_key().approval_key

    def issue_approval_key(self, max_retries: int = 3) -> ApprovalResponse:
        """POST /oauth2/Approval (재시도 로직 포함)"""
        url = f"{self.cfg.base_url}/oauth2/Approval"
        headers = {"content-type": "application/json; charset=utf-8"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.cfg.app_key,
            "secretkey": self.cfg.app_secret,
        }

        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.post(url, headers=headers, json=body, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                approval = ApprovalResponse.from_json(data)
                self._approval = approval
                self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.validity_seconds)
                self._save_cache()
                return approval
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries:
                    wait_time = attempt * 2  # 2초, 4초, 6초...
                    logger.warning("Retry in %d seconds... (%d/%d)", wait_time, attempt, max_retries)
                    time.sleep(wait_time)
                else:
                    raise
```

**특징**:
- **24시간 유효기간**: Approval Key는 발급 후 24시간 유효
- **재시도 로직**: 네트워크 오류 시 최대 3회 재시도
- **파일 캐싱**: 재시작 시에도 캐시된 키 재사용
- **환경변수 지원**: `KIS_TOKEN_CACHE_DIR`로 캐시 경로 커스터마이징

**캐시 파일 구조** (`token_cache_ws.json`):
```json
{
  "approval_key": "f8ab3c2e-1234-5678-9abc-def012345678",
  "expires_at": "2026-01-06T10:30:00+00:00"
}
```

---

### 6.4 KisWsClient: WebSocket 메시지 생성

**파일**: [kis_ws_client.py](../services/market-data/src/quote_pipeline/clients/kis/kis_ws_client.py)

KisWsClient는 WebSocket 메시지 생성 및 헬퍼 메서드를 제공합니다.

#### 6.4.1 WebSocket 메시지 생성

```python
class KisWsClient:
    """한투 WebSocket 메시지 빌더"""

    def __init__(self, config: KisConfig, auth_client: KisWsAuthClient):
        self.cfg = config
        self.auth = auth_client
        self.approval_key: str | None = None

    def issue_approval_key(self) -> str:
        """승인키 발급/캐시 (KisWsAuthClient에 위임)"""
        self.approval_key = self.auth.get_valid_approval_key()
        return self.approval_key

    def _build_ws_message(self, tr_id: str, tr_key: str, tr_type: str = "1") -> str:
        """
        WebSocket 메시지 생성

        Args:
            tr_id: H0UNCNT0 또는 HDFSCNT0
            tr_key: 구독 키 (국내: 심볼, 해외: D{exchange}{symbol})
            tr_type: "1" (등록) 또는 "2" (해제)

        Returns:
            JSON 문자열
        """
        if not self.approval_key:
            raise RuntimeError("approval_key 없음. issue_approval_key() 먼저 호출 필요")

        msg = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": tr_type,
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": tr_key,
                }
            },
        }
        return json.dumps(msg)
```

#### 6.4.2 WebSocket 메시지 예시

**국내주식 등록 (H0UNCNT0)**:
```json
{
  "header": {
    "approval_key": "f8ab3c2e-1234-5678-9abc-def012345678",
    "custtype": "P",
    "tr_type": "1",
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "H0UNCNT0",
      "tr_key": "005930"
    }
  }
}
```

**해외주식 등록 (HDFSCNT0)**:
```json
{
  "header": {
    "approval_key": "f8ab3c2e-1234-5678-9abc-def012345678",
    "custtype": "P",
    "tr_type": "1",
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "HDFSCNT0",
      "tr_key": "DNASNVDA"
    }
  }
}
```

**구독 해제 (tr_type="2")**:
```json
{
  "header": {
    "approval_key": "...",
    "custtype": "P",
    "tr_type": "2",  // 해제
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "HDFSCNT0",
      "tr_key": "DNASNVDA"
    }
  }
}
```

#### 6.4.3 테스트용 헬퍼 메서드

```python
async def subscribe_domestic_ticks(
    self,
    symbols: Iterable[str],
    message_handler=None,
):
    """국내주식 실시간 체결가 구독 (테스트용)"""
    tr_id = KisTrId.DOMESTIC_TICK.value
    uri = f"{self.cfg.ws_base_url}{get_ws_endpoint(tr_id)}"

    async with websockets.connect(uri, ping_interval=30) as ws:
        for code in symbols:
            sub = KisSubscription.for_domestic(code)
            req = self._build_ws_message(sub.tr_id, sub.tr_key, KisTrType.REGISTER)
            await ws.send(req)

        while True:
            msg = await ws.recv()
            if message_handler:
                message_handler(msg)
            else:
                print("DOMESTIC:", msg)
```

---

### 6.5 KisClient: WebSocket 라이프사이클 관리

**파일**: [kis_client.py](../services/market-data/src/quote_pipeline/clients/kis/kis_client.py)

KisClient는 BaseClient를 구현하며, WebSocket 연결 및 구독 관리를 담당합니다.

#### 6.5.1 클래스 구조

```python
class KisClient(BaseClient):
    """KIS WebSocket 클라이언트"""

    def __init__(
        self,
        config: KisConfig,
        auth_client: KisWsAuthClient,
        subscription_service: SubscriptionService,
        symbol_service: SymbolService,
    ):
        self.config = config
        self.auth_client = auth_client
        self.subscription_service = subscription_service
        self.symbol_service = symbol_service

        self.ws_client = KisWsClient(config, auth_client)
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.desired_symbols: Set[str] = set()
```

**의존성**:
- **config**: KIS 설정 (API 키, URL)
- **auth_client**: Approval Key 발급 및 캐싱
- **subscription_service**: 구독 상태 추적 (중복 구독 방지, 증분 계산)
- **symbol_service**: 심볼 메타데이터 조회 (national, exchange)

#### 6.5.2 connect(): WebSocket 연결

```python
async def connect(self) -> None:
    """
    KIS WebSocket 서버에 연결합니다.

    1. Approval Key 발급 (캐시에서 재사용 또는 신규 발급)
    2. WebSocket 연결 수립
    """
    if self.ws is not None:
        logger.warning("[KisClient] Already connected")
        return

    # 1. Approval Key 발급
    logger.info("[KisClient] Issuing approval key...")
    self.ws_client.issue_approval_key()
    logger.info("[KisClient] Approval key issued successfully")

    # 2. WebSocket 연결
    uri = self.ws_client.cfg.ws_base_url
    logger.info("[KisClient] Connecting to WebSocket: %s", uri)
    self.ws = await websockets.connect(uri, ping_interval=30)
    logger.info("[KisClient] WebSocket connected successfully")
```

#### 6.5.3 subscribe(): 초기 심볼 구독

```python
async def subscribe(self, symbols: Iterable[str]) -> None:
    """
    심볼 구독을 등록합니다.

    Args:
        symbols: 구독할 심볼 리스트 (예: ["005930", "NVDA", "AAPL"])
    """
    if not self.ws:
        raise RuntimeError("[KisClient] Not connected. Call connect() first.")

    self.desired_symbols = set(symbols)

    for symbol in symbols:
        await self._subscribe_symbol(symbol)
```

#### 6.5.4 _subscribe_symbol(): 개별 심볼 구독

```python
async def _subscribe_symbol(self, symbol: str) -> None:
    """
    개별 심볼을 구독합니다.

    흐름:
    1. SymbolService에서 메타데이터 조회 (national, exchange)
    2. build_subscription()으로 구독 정보 생성 (tr_id, tr_key)
    3. 이미 구독 중이면 스킵
    4. WebSocket 구독 메시지 전송
    5. SubscriptionService에 구독 상태 기록
    """
    # 1. 메타데이터 조회
    metadata = self.symbol_service.get_metadata_by_symbol(symbol)
    national = metadata.national
    exchange = metadata.exchange

    logger.info(
        "[KisClient] Symbol metadata: symbol=%s, national=%s, exchange=%s",
        symbol, national, exchange
    )

    # 2. 구독 정보 생성
    if national == "KR":
        sub = build_subscription(symbol, national, exchange=None)
    else:
        sub = build_subscription(symbol, national, exchange=exchange)

    logger.info(
        "[KisClient] Built subscription: tr_id=%s, tr_key=%s, symbol=%s",
        sub.tr_id, sub.tr_key, sub.symbol
    )

    # 3. 중복 구독 체크
    if self.subscription_service.is_subscribed(sub.tr_id, symbol):
        logger.debug("[KisClient] Already subscribed: %s (%s)", symbol, sub.tr_id)
        return

    # 4. 구독 메시지 전송
    req = self.ws_client._build_ws_message(sub.tr_id, sub.tr_key, KisTrType.REGISTER)
    logger.info("[KisClient] Sending subscribe request: %s", req)
    await self.ws.send(req)

    # 5. 구독 상태 기록
    self.subscription_service.mark_subscribed(sub.tr_id, symbol, sub.tr_key)
    logger.info("[KisClient][%s] Subscribed %s (%s)", sub.tr_id, symbol, sub.tr_key)
```

**예시 로그**:
```
[KisClient] Symbol metadata: symbol=005930, national=KR, exchange=None
[KisClient] Built subscription: tr_id=H0UNCNT0, tr_key=005930, symbol=005930
[KisClient] Sending subscribe request: {"header":{"approval_key":"...","tr_type":"1"},...}
[KisClient][H0UNCNT0] Subscribed 005930 (005930)

[KisClient] Symbol metadata: symbol=NVDA, national=US, exchange=NAS
[KisClient] Built subscription: tr_id=HDFSCNT0, tr_key=DNASNVDA, symbol=NVDA
[KisClient][HDFSCNT0] Subscribed NVDA (DNASNVDA)
```

#### 6.5.5 apply_symbols(): 동적 구독 변경

```python
async def apply_symbols(self, symbols: Iterable[str]) -> None:
    """
    동적으로 구독 심볼을 변경합니다.

    WebSocket 재연결 없이 구독 목록을 변경합니다.

    흐름:
    1. 원하는 구독 목록 생성 (심볼 → tr_id, tr_key 매핑)
    2. SubscriptionService.calculate_changes()로 증분 계산
    3. 구독 해제 (to_remove)
    4. 구독 등록 (to_add)
    """
    if not self.ws:
        raise RuntimeError("[KisClient] Not connected. Call connect() first.")

    self.desired_symbols = set(symbols)

    # 1. 원하는 구독 목록 생성: (tr_id, symbol) -> tr_key
    desired_subs = {}
    for sym in self.desired_symbols:
        try:
            metadata = self.symbol_service.get_metadata_by_symbol(sym)
            national = metadata.national
            exchange = metadata.exchange

            if national == "KR":
                sub = build_subscription(sym, national, exchange=None)
            else:
                sub = build_subscription(sym, national, exchange=exchange)

            desired_subs[(sub.tr_id, sym)] = sub.tr_key
        except SymbolNotFoundError:
            logger.warning("[KisClient] Symbol '%s' not found, skipping", sym)
            continue

    # 2. 구독 변경사항 계산
    to_add, to_remove = self.subscription_service.calculate_changes(desired_subs)

    if to_add or to_remove:
        logger.info("[KisClient] Apply: add=%d remove=%d", len(to_add), len(to_remove))

    # 3. 구독 해제
    for (tr_id, sym), tr_key in to_remove.items():
        req = self.ws_client._build_ws_message(tr_id, tr_key, KisTrType.UNREGISTER)
        await self.ws.send(req)
        self.subscription_service.mark_unsubscribed(tr_id, sym)
        logger.info("[KisClient][%s] Unsubscribed %s (%s)", tr_id, sym, tr_key)

    # 4. 구독 등록
    for (tr_id, sym), tr_key in to_add.items():
        req = self.ws_client._build_ws_message(tr_id, tr_key, KisTrType.REGISTER)
        await self.ws.send(req)
        self.subscription_service.mark_subscribed(tr_id, sym, tr_key)
        logger.info("[KisClient][%s] Subscribed %s (%s)", tr_id, sym, tr_key)
```

**동적 구독 변경 예시**:

```python
# 초기 구독: 005930, NVDA
await kis_client.subscribe(["005930", "NVDA"])
# → H0UNCNT0: 005930
# → HDFSCNT0: DNASNVDA

# Redis에서 심볼 변경: 005930 제거, AAPL 추가
# Redis: SADD active_symbols:kis_new AAPL
# Redis: SREM active_symbols:kis_new 005930

# apply_symbols() 호출
await kis_client.apply_symbols(["NVDA", "AAPL"])
# → Unsubscribe: 005930 (H0UNCNT0)
# → Subscribe: AAPL (HDFSCNT0)
# → 최종 구독: NVDA, AAPL
```

#### 6.5.6 receive(): 메시지 수신

```python
async def receive(self) -> str:
    """
    WebSocket에서 메시지를 수신합니다.

    Returns:
        수신된 raw 메시지 (파싱은 MessageParser에서 처리)
    """
    if not self.ws:
        raise RuntimeError("[KisClient] Not connected. Call connect() first.")

    msg = await self.ws.recv()
    logger.debug("[KisClient] Received message (len=%d)", len(msg))
    return msg  # type: ignore
```

#### 6.5.7 close(): 연결 종료

```python
async def close(self) -> None:
    """WebSocket 연결을 종료하고 구독 상태를 초기화합니다."""
    if self.ws:
        await self.ws.close()
        self.ws = None
        self.subscription_service.clear()
        logger.info("[KisClient] Connection closed")
```

---

### 6.6 전체 흐름 요약

#### 6.6.1 초기 연결 및 구독

```
1. KisClient 생성
   ├── KisConfig (app_key, app_secret)
   ├── KisWsAuthClient (Approval Key 관리)
   ├── KisWsClient (메시지 빌더)
   ├── SymbolService (심볼 메타데이터)
   └── SubscriptionService (구독 상태 추적)

2. connect()
   ├── KisWsAuthClient.get_valid_approval_key()
   │   ├── 캐시에서 로드 (유효기간 체크)
   │   └── 만료 시: POST /oauth2/Approval (재시도 로직)
   └── websockets.connect(ws_base_url)

3. subscribe(["005930", "NVDA"])
   └── for each symbol:
       ├── SymbolService.get_metadata_by_symbol(symbol)
       │   └── (national, exchange) 조회
       ├── build_subscription(symbol, national, exchange)
       │   ├── 국내(KR): tr_id=H0UNCNT0, tr_key=symbol
       │   └── 해외(US): tr_id=HDFSCNT0, tr_key=D{exchange}{symbol}
       ├── SubscriptionService.is_subscribed() 체크
       ├── KisWsClient._build_ws_message(tr_id, tr_key, "1")
       ├── ws.send(message)
       └── SubscriptionService.mark_subscribed(tr_id, symbol, tr_key)
```

#### 6.6.2 동적 구독 변경 (apply_symbols)

**동적 모드 전체 흐름** ([ingestor_manager.py](../services/market-data/src/quote_pipeline/ingestors/ingestor_manager.py)):

```
1. IngestorManager 시작 (동적 모드)
   └── _run_dynamic_symbol_loop(provider)
       │
       ├── 초기 심볼 로드
       │   └── _get_symbols_from_redis(provider)
       │       └── Redis SMEMBERS "active_symbols:kis_new"
       │
       ├── ingestor 시작 (초기 심볼로)
       │
       └── [폴링 루프 - 5초마다]
           │
           ├── await asyncio.sleep(poll_interval_s)  # 기본 5초
           │
           ├── new_symbols = _get_symbols_from_redis(provider)
           │   └── Redis SMEMBERS "active_symbols:kis_new"
           │
           ├── if new_symbols == current_symbols:
           │   └── continue  # 변경 없으면 스킵
           │
           ├── logger.info("Symbols changed: %s → %s", current_symbols, new_symbols)
           │
           ├── if hasattr(ingestor.client, "apply_symbols"):
           │   │   # KisClient는 apply_symbols 지원
           │   └── await ingestor.apply_symbols(new_symbols)  ← 아래 상세 흐름
           │
           └── else:
               │   # apply_symbols 미지원 시 ingestor 재시작
               ├── task.cancel()
               └── task, ingestor = start_ingestor(new_symbols)
```

**사용자 → Redis 심볼 변경**:

```bash
# 심볼 추가
redis-cli SADD active_symbols:kis_new TSLA

# 심볼 제거
redis-cli SREM active_symbols:kis_new 005930

# 현재 심볼 확인
redis-cli SMEMBERS active_symbols:kis_new
```

**apply_symbols() 내부 흐름** ([kis_client.py](../services/market-data/src/quote_pipeline/clients/kis/kis_client.py)):

```
apply_symbols(new_symbols)
   ├── desired_subs = {}  # (tr_id, symbol) -> tr_key
   ├── for sym in new_symbols:
   │   ├── metadata = SymbolService.get_metadata_by_symbol(sym)
   │   ├── sub = build_subscription(sym, metadata.national, metadata.exchange)
   │   └── desired_subs[(sub.tr_id, sym)] = sub.tr_key
   │
   ├── to_add, to_remove = SubscriptionService.calculate_changes(desired_subs)
   │   # 현재 구독과 비교하여 증분 계산
   │
   ├── for (tr_id, sym), tr_key in to_remove.items():
   │   ├── ws.send({"tr_type": "2", "tr_id": tr_id, "tr_key": tr_key})
   │   └── SubscriptionService.mark_unsubscribed(tr_id, sym)
   │
   └── for (tr_id, sym), tr_key in to_add.items():
       ├── ws.send({"tr_type": "1", "tr_id": tr_id, "tr_key": tr_key})
       └── SubscriptionService.mark_subscribed(tr_id, sym, tr_key)
```

**전체 데이터 흐름 요약**:

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐
│ 사용자/API    │────▶│  Redis Set         │────▶│IngestorManager│
│              │     │ active_symbols:    │     │(5초 폴링)     │
│ SADD/SREM    │     │ kis_new            │     └──────┬───────┘
└──────────────┘     └────────────────────┘            │
                                                        ▼
                                           ┌────────────────────┐
                                           │ ingestor.          │
                                           │ apply_symbols()    │
                                           └────────┬───────────┘
                                                    ▼
                                           ┌────────────────────┐
                                           │ KisClient.         │
                                           │ apply_symbols()    │
                                           └────────┬───────────┘
                                                    ▼
                                           ┌────────────────────┐
                                           │ SubscriptionService│
                                           │ .calculate_changes()│
                                           └────────┬───────────┘
                                                    ▼
                                           ┌────────────────────┐
                                           │ WebSocket 구독     │
                                           │ REGISTER/UNREGISTER│
                                           └────────────────────┘
```

#### 6.6.3 메시지 수신 및 파싱

```
1. receive() → raw message
   └── ws.recv()

2. KisMessageParser.parse(message)
   ├── tr_id 감지 (H0UNCNT0 / HDFSCNT0)
   ├── H0UNCNT0: KisDomesticQuoteDTO
   ├── HDFSCNT0: KisOverseasQuoteDTO
   └── 기타: KisSubscriptionResponseDTO

3. KisQuoteMapper.to_uni_quote(dto)
   └── UniQuoteDto (통합 시세)

4. Publisher.publish(uni_quote)
   ├── RedisPublisher: HSET + PUBLISH
   └── StdoutPublisher: print(uni_quote)
```

---

### 6.7 SubscriptionService: 구독 상태 관리

**역할**: 중복 구독 방지 및 구독 증분을 계산해서 메모리 값에 갱신

```python
class SubscriptionService:
    """구독 상태 추적 서비스"""

    def __init__(self):
        # (tr_id, symbol) -> tr_key
        self._subscriptions: Dict[Tuple[str, str], str] = {}

    def is_subscribed(self, tr_id: str, symbol: str) -> bool:
        """이미 구독 중인지 확인"""
        return (tr_id, symbol) in self._subscriptions

    def mark_subscribed(self, tr_id: str, symbol: str, tr_key: str) -> None:
        """구독 상태 기록"""
        self._subscriptions[(tr_id, symbol)] = tr_key

    def mark_unsubscribed(self, tr_id: str, symbol: str) -> None:
        """구독 해제 기록"""
        self._subscriptions.pop((tr_id, symbol), None)

    def calculate_changes(
        self,
        desired: Dict[Tuple[str, str], str]
    ) -> Tuple[Dict, Dict]:
        """
        증분 구독 계산

        Args:
            desired: 원하는 구독 목록 {(tr_id, symbol): tr_key}

        Returns:
            (to_add, to_remove)
        """
        current_keys = set(self._subscriptions.keys())
        desired_keys = set(desired.keys())

        to_add = {k: desired[k] for k in desired_keys - current_keys}
        to_remove = {k: self._subscriptions[k] for k in current_keys - desired_keys}

        return to_add, to_remove

    def clear(self) -> None:
        """모든 구독 상태 초기화"""
        self._subscriptions.clear()
```

**예시**:

```python
# 초기 구독
service.mark_subscribed("H0UNCNT0", "005930", "005930")
service.mark_subscribed("HDFSCNT0", "NVDA", "DNASNVDA")

# 구독 변경: 005930 제거, AAPL 추가
desired = {
    ("HDFSCNT0", "NVDA"): "DNASNVDA",
    ("HDFSCNT0", "AAPL"): "DNYSAAPL",
}

to_add, to_remove = service.calculate_changes(desired)
# to_add = {("HDFSCNT0", "AAPL"): "DNYSAAPL"}
# to_remove = {("H0UNCNT0", "005930"): "005930"}
```

---

### 6.8 SymbolService: 심볼 메타데이터 조회

**역할**: 심볼 → (national, exchange) 조회 및 메모리 캐싱

```python
@dataclass
class SymbolMetadata:
    symbol: str
    national: str
    exchange: str | None

class SymbolService:
    """심볼 메타데이터 조회 및 캐싱"""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        # 캐시: {symbol: SymbolMetadata}
        self._cache: Dict[str, SymbolMetadata] = {}

    async def load_cache_from_db(self):
        """DB에서 심볼 메타데이터 로드"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT symbol, national, exchange FROM securities_master"
            )
            for row in rows:
                metadata = SymbolMetadata(
                    symbol=row["symbol"],
                    national=row["national"],
                    exchange=row["exchange"],
                )
                self._cache[row["symbol"]] = metadata

    def get_metadata_by_symbol(self, symbol: str) -> SymbolMetadata:
        """캐시에서 심볼 메타데이터 조회"""
        metadata = self._cache.get(symbol)
        if not metadata:
            raise SymbolNotFoundError(f"Symbol {symbol} not found in cache")
        return metadata
```

**DB 스키마** (`securities_master`):

| symbol | national | exchange |
|--------|----------|----------|
| 005930 | KR | NULL |
| 196170 | KR | NULL |
| NVDA | US | NAS |
| AAPL | US | NAS |
| AA | US | NYS |
| 5 | HK | HKS |

---

## 7. 실행 가이드

### 7.1 Docker 환경

```bash
# 전체 실행
docker compose up -d postgres redis
docker compose up --build market-data

# 로그 확인
docker compose logs -f market-data
```

### 7.2 로컬 개발

```bash
# 1. 의존성 설치
cd services/market-data
uv sync

# 2. 환경변수 설정
export PYTHONPATH=src
export KIS_APP_KEY=...
export KIS_APP_SECRET=...

# 3. 실행
uv run -m quote_pipeline.main
```

### 7.3 Redis 명령어

```bash
# 심볼 추가
redis-cli SADD active_symbols:kis_new TSLA

# 심볼 제거
redis-cli SREM active_symbols:kis_new NVDA

# 현재 심볼 확인
redis-cli SMEMBERS active_symbols:kis_new

# 시세 조회
redis-cli HGETALL quote:US:NAS:NVDA
redis-cli HGETALL quote:KR:KOSPI:005930
```

### 7.4 운영 유틸리티 (manage.py)

```bash
# 대화형 모드
uv run -m quote_pipeline.manage

# 심볼 목록 조회
uv run -m quote_pipeline.manage symbols list kis_new

# 시세 조회
uv run -m quote_pipeline.manage quotes get NVDA
```

---

## 8. 리팩토링 히스토리

### 8.1 개선 전 (v1.0)

**문제점**:
- KisIngestor가 372줄 (파싱, DB 쿼리, WebSocket 관리 모두 포함)
- 파서와 ingestor 강하게 결합
- DB 쿼리가 생성자에서 직접 호출 (테스트 어려움)
- Provider별 페이로드 구조 불일치

### 8.2 개선 후 (v2.0)

**핵심 변경사항**:

| 기존 | 변경 후 | 이유 |
|-----|--------|-----|
| `KisIngestor` (372줄) | `KisClient` (50줄) + `KisParser` (100줄) + `KisMapper` (30줄) + `BaseIngestor` (150줄) | 책임 분리 |
| 파서 함수 in ingestor | `parsers/kis_message_parser.py` | 재사용성, 테스트 용이성 |
| DB 쿼리 in 생성자 | `services/symbol_service.py` | 의존성 주입, 테스트 가능 |
| 구독 상태 in ingestor | `services/subscription_service.py` | 상태 관리 캡슐화 |

**성과**:

| 항목 | 개선 전 | 개선 후 | 효과 |
|-----|--------|--------|------|
| **코드 구조** | KisIngestor 372줄 | 7개 클래스로 분리 | 단일 책임 원칙 (SRP) |
| **테스트 용이성** | 통합 테스트만 가능 | 각 레이어 단위 테스트 가능 | Mock 활용 가능 |
| **확장성** | provider 추가 시 전체 수정 | Client + Parser + Mapper만 구현 | 기존 코드 영향 없음 |
| **유지보수성** | 변경 영향 범위 불명확 | 레이어별 책임 명확 | 변경 영향 최소화 |

### 8.3 Hexagonal Architecture 적용

```
포트와 어댑터 패턴:
- 입력 포트 (Clients): 외부 시스템과의 통신
- 출력 포트 (Publishers): 데이터 발행
- 도메인 로직 (Services): 재사용 가능한 비즈니스 로직
- 인프라 (Infrastructure): DB, Redis 등
```

---

## 부록 A. 관련 문서

- [Active Symbol 관리](./active_symbol.md) - 동적 심볼 관리 상세
- [DB Schema](./db_schema.md) - 종목 마스터 테이블
- [Spring Boot R2DBC](./springboot_r2dbc.md) - Core API 연동

---

## 부록 B. Outdate된 설계 히스토리

### B.1 pykis 라이브러리 기반 (Deprecated)

**사용 시기**: 2024-Q4
**파일**: `ingestors/kis_ingestor.py` (레거시)

**변경 이유**:
- pykis 라이브러리의 제한적인 커스터마이징
- 동적 구독 기능 미지원
- WebSocket 재연결 로직 불안정

**현재 상태**: `clients/kis/kis_client.py`로 직접 구현으로 전환

### B.2 KIS Pure Flow (실험적)

**사용 시기**: 2025-Q1
**파일**: `clients/kis/kis_main.py` (별도 실행)

**목적**:
- KIS OpenAPI REST/WebSocket 테스트
- 인증 토큰 캐싱 로직 검증

**현재 상태**: 테스트 용도로만 유지, 실제 파이프라인에는 미사용

---