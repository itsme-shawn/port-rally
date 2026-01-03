# CLAUDE.md - PortRally Project Guide for AI Assistants

> Last Updated: 2026-01-03
> This document provides AI assistants with essential context about the PortRally codebase structure, conventions, and workflows.

## Project Overview

PortRally is an AI-powered real-time portfolio management and insights platform for individual investors (beginner to intermediate level). The platform provides:

1. Real-time Dashboard: Portfolio heatmap, balance/P&L tracking, top movers
2. AI Insights: Risk scoring, concentration/correlation analysis, LLM-based natural language reports, rebalancing recommendations
3. Real-time Alerts: Price, volatility, and news-based push notifications

## Critical Context

### Technology Stack

```
Frontend:  Next.js + Tailwind CSS + Zustand (planned, not yet implemented)
Backend:   Spring Boot 3.5.8 + WebFlux (Reactive) + R2DBC
Data:      PostgreSQL 16 + Redis 7
Market:    Python 3.12 + WebSocket clients (Upbit, Binance, KIS)
AI:        Python + FastAPI + LLM (planned, not yet implemented)
Infra:     Docker Compose, Kafka (planned)
```

### Repository Structure

```
port-rally/                          # Monorepo root
├── apps/
│   ├── core-api/                    # Spring Boot WebFlux backend (PRIMARY)
│   │   ├── src/main/java/api/
│   │   │   ├── config/              # R2DBC, Security, Exception handling
│   │   │   ├── controller/          # REST endpoints
│   │   │   ├── service/             # Business logic
│   │   │   ├── domain/              # JPA entities (17 entities)
│   │   │   ├── repository/          # R2DBC repositories (16 repos)
│   │   │   ├── dto/                 # Request/Response DTOs
│   │   │   └── enums/               # Enums (13 types)
│   │   ├── src/main/resources/
│   │   │   ├── application.yml      # Main configuration
│   │   │   ├── application-local.yml # Local dev overrides
│   │   │   └── db/migration/        # Flyway SQL migrations (8 files)
│   │   ├── build.gradle             # Dependencies (WebFlux, R2DBC, Redis, Security)
│   │   └── run-local.sh             # Local development script
│   └── web/                         # Next.js frontend (PLANNED)
├── services/
│   ├── market-data/                 # Python market data pipeline (ACTIVE)
│   │   ├── src/quote_pipeline/
│   │   │   ├── main.py              # Entry point
│   │   │   ├── clients/             # Upbit, Binance, KIS WebSocket clients
│   │   │   ├── publishers/          # Redis Pub/Sub publisher
│   │   │   └── utils/               # Trading hours, helpers
│   │   └── pyproject.toml           # Python dependencies (websockets, redis, python-kis)
│   └── ai-agent/                    # AI agent service (PLANNED)
├── packages/                        # Shared libraries (PLANNED)
├── infrastructure/                  # Infrastructure configs (PLANNED)
├── docs/                            # Documentation
│   ├── 01_project_summary.md        # Project goals and KPIs
│   ├── 02_core_architecture.md      # System architecture
│   ├── 03_marketdata_pipeline.md    # Market data flow
│   ├── 04_ondemand_symbol_streaming.md
│   ├── 05_development_phases.md     # Development roadmap
│   └── draft/                       # Working documents
├── docker-compose.yml               # Production infrastructure
├── docker-compose.override.yml      # Local development overrides
├── AGENTS.md                        # Quick reference for agents
├── README.md                        # Setup and usage guide
└── .env                             # Environment variables (gitignored)
```

## Architecture Overview

### Data Flow

```
Exchange WebSocket (Upbit/Binance/KIS)
  ↓
services/market-data (Python Ingestor)
  ↓
Redis Pub/Sub (quotes.tick) + Redis Cache (quote:<symbol>)
  ↓
apps/core-api (Spring WebFlux)
  ├─→ REST API (current price lookup)
  └─→ WebSocket Gateway (real-time push to clients)
  ↓
apps/web (Next.js client)
```

### Key Redis Data Structures

| Key Pattern | Type | Purpose |
|-------------|------|---------|
| `quotes.tick` | Pub/Sub Channel | Real-time normalized tick events from ingestors |
| `quote:<symbol>` | Hash | Current price cache (fields: price, ts) |
| `active_symbols` | Set | Symbols to subscribe (managed by API server) |

### Database Schema (PostgreSQL)

19 tables across 7 migration files:
- User Management: users, social_accounts, user_preferences
- Assets: assets_master, assets_metrics, asset_ai_insights
- Portfolio: portfolios, positions, portfolio_metrics, portfolio_ai_insights
- OCR: uploaded_images, ocr_results, ocr_detected_positions
- News: news_articles, news_asset_relations
- Notifications: notification_types, user_notification_settings, notifications_logs
- Audit: audit_logs

### Current Implementation Status

#### Phase 0 (Market Data PoC) - COMPLETED
- ✅ Upbit/Binance/KIS WebSocket clients
- ✅ Redis Pub/Sub pipeline
- ✅ Quote normalization and caching
- ✅ Docker Compose infrastructure

#### Phase 1 (Core API) - IN PROGRESS
- ✅ Spring Boot 3.5.8 + WebFlux setup
- ✅ R2DBC + Flyway configuration
- ✅ Database schema (19 tables)
- ✅ Domain entities and repositories
- ✅ Basic User API (MVP)
- ⏳ OAuth2/JWT authentication (PLANNED)
- ⏳ Portfolio/Asset CRUD (PLANNED)
- ⏳ WebSocket Gateway (PLANNED)

#### Phase 2-5 - PLANNED
- ⏳ Kafka integration
- ⏳ Next.js web frontend
- ⏳ AI agent service
- ⏳ Advanced AI insights

## Development Workflows

### Local Development Setup

```bash
# 1. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
uv python install 3.12                            # Install Python 3.12

# 2. Start infrastructure (Redis + PostgreSQL)
docker compose up -d postgres redis

# 3. Run market-data service locally (optional)
cd services/market-data
uv venv --python 3.12
source .venv/bin/activate
uv sync
export PYTHONPATH=src
uv run -m quote_pipeline.main \
  --provider upbit \
  --symbols KRW-BTC,KRW-ETH \
  --redis-url redis://localhost:6379/0 \
  --redis-channel quotes

# 4. Run Spring Boot API locally
./run-local.sh
# OR
cd apps/core-api
DB_HOST=localhost ./gradlew bootRun --args='--spring.profiles.active=local'

# 5. Verify services
# API Health: http://localhost:8080/actuator/health
# Swagger UI: http://localhost:8080/swagger-ui.html
# Redis: redis-cli -u redis://localhost:6379/0 SUBSCRIBE quotes
```

### Docker Compose Management

```bash
# Start all services
docker compose up -d

# Rebuild specific service
docker compose up -d --build <service>  # market-data, core-api, redis, postgres

# View logs
docker compose logs -f <service>

# Restart service
docker compose restart <service>

# Stop all services
docker compose down          # Keep volumes
docker compose down -v       # Delete volumes (⚠️ data loss)
```

### Testing

#### Python (market-data)
```bash
cd services/market-data
uv run -m pytest tests/
uv run -m pytest tests/ --cov=quote_pipeline
```

#### Java (core-api)
```bash
cd apps/core-api
./gradlew test
./gradlew test --tests "api.service.*"
```

### Git Workflow

Current branch: `claude/claude-md-mjy2fbvak9gobbq8-6qRVE`

All development should occur on designated `claude/*` branches. Follow these practices:

1. Make focused, atomic commits
2. Use descriptive commit messages with prefixes:
   - `[feat]` - New features
   - `[fix]` - Bug fixes
   - `[docs]` - Documentation updates
   - `[refactor]` - Code refactoring
   - `[test]` - Test additions/changes
   - `[chore]` - Build/config changes

Example commit messages from repository:
```
[docs] (core-api) springboot, DB 관련 작업사항 문서 업데이트
[feat] (core-api) Exception 로깅 관련 설정
[feat] (infra) Docker Compose 업데이트
```

## Code Conventions

### Java (Spring Boot)

1. Package Structure:
   - `api.config.*` - Configuration classes
   - `api.controller.*` - REST controllers
   - `api.service.*` - Business logic services
   - `api.domain.*` - JPA entities
   - `api.repository.*` - R2DBC repositories
   - `api.dto.*` - Data transfer objects
   - `api.enums.*` - Enumeration types

2. Naming Conventions:
   - Controllers: `*Controller.java`
   - Services: `*Service.java`
   - Repositories: `*Repository.java`
   - DTOs: `*Request.java`, `*Response.java`
   - Configs: `*Config.java`

3. Reactive Programming:
   - Use `Mono<T>` for single values
   - Use `Flux<T>` for streams
   - Avoid blocking operations in reactive chains
   - Use `.subscribeOn()` and `.publishOn()` appropriately

4. Database:
   - Use Flyway migrations for schema changes (never modify existing migrations)
   - Follow naming: `V{number}__{description}.sql`
   - Entities use `@Table`, `@Id`, `@Column` annotations
   - Use R2DBC repositories extending `R2dbcRepository`

### Python (market-data)

1. Project Structure:
   - `src/quote_pipeline/` - Main package
   - `src/quote_pipeline/clients/` - Exchange clients
   - `src/quote_pipeline/publishers/` - Redis publishers
   - `src/quote_pipeline/utils/` - Utilities
   - `tests/` - Test files mirroring src structure

2. Naming Conventions:
   - Files: snake_case (e.g., `redis_publisher.py`)
   - Classes: PascalCase (e.g., `RedisPublisher`)
   - Functions/Variables: snake_case
   - Constants: UPPER_SNAKE_CASE

3. Dependencies:
   - Use `uv` for package management
   - Add dependencies to `pyproject.toml`
   - Run `uv sync` after changes

4. Async Programming:
   - Use `async/await` for I/O operations
   - WebSocket clients are async
   - Redis operations are async

### Documentation

1. Markdown files should be readable in plain text (minimal bold/italics per AGENTS.md:48)
2. Code documentation:
   - Java: JavaDoc for public APIs
   - Python: Docstrings for classes and functions
3. Update relevant docs in `docs/` when making architectural changes
4. Update `docs/draft/springboot_work_log.md` for Spring Boot changes

## Common Tasks for AI Assistants

### Adding a New REST Endpoint

1. Create DTO classes in `apps/core-api/src/main/java/api/dto/<domain>/`
2. Add service method in `apps/core-api/src/main/java/api/service/<domain>/*Service.java`
3. Add controller endpoint in `apps/core-api/src/main/java/api/controller/*Controller.java`
4. If new entities needed, create Flyway migration first
5. Test using Swagger UI at http://localhost:8080/swagger-ui.html

### Adding Database Tables

1. Create migration file: `apps/core-api/src/main/resources/db/migration/V{next}__{description}.sql`
2. Create entity in `apps/core-api/src/main/java/api/domain/`
3. Create repository in `apps/core-api/src/main/java/api/repository/`
4. Restart Spring Boot to apply migration
5. Update `docs/draft/springboot_work_log.md`

### Adding a New Market Data Provider

1. Create client class in `services/market-data/src/quote_pipeline/clients/<provider>/`
2. Implement WebSocket connection and message parsing
3. Normalize data to common format
4. Publish to Redis using `RedisPublisher`
5. Add tests in `services/market-data/tests/`
6. Update documentation

### Debugging Issues

#### Check Spring Boot Logs
```bash
docker compose logs -f core-api
# Look for startup errors, SQL queries, exceptions
```

#### Check Market Data Pipeline
```bash
docker compose logs -f market-data
# Look for WebSocket connections, Redis publishing
```

#### Verify Redis Operations
```bash
redis-cli -u redis://localhost:6379/0
> SUBSCRIBE quotes           # Monitor real-time ticks
> GET quote:KRW-BTC         # Check cached price
> SMEMBERS active_symbols   # Check subscribed symbols
```

#### Check Database State
```bash
docker compose exec postgres psql -U portrally -d portrally
\dt                         # List tables
\d users                    # Describe table
SELECT * FROM flyway_schema_history;  # Check migrations
```

## Important Notes

### Security & Compliance

1. Never commit `.env` files (contains API keys, passwords)
2. Investment advice disclaimer required (regulatory compliance)
3. Encrypt user asset/order data
4. Secure API token storage (Vault/Secrets Manager in production)
5. Maintain audit logs for all operations

### Performance Considerations

1. Redis is for speed (real-time quotes), Kafka is for reliability (AI jobs)
2. WebSocket connections should handle reconnection gracefully
3. Rate limiting required for exchange APIs
4. Monitor subscription counts to avoid connection limits
5. Use Redis Pub/Sub for real-time data (lossy but fast)

### Testing Requirements

1. Unit tests required for business logic
2. Integration tests with Testcontainers (Spring Boot)
3. Mock external APIs in tests
4. Test async/reactive code with `reactor-test` (Java) and `pytest-asyncio` (Python)

### Development Phases

Current focus: Phase 1 (Core API)

Priority order:
1. P0: Market data PoC (DONE) - Validate WebSocket stability
2. P1: Core API (IN PROGRESS) - Authentication, Portfolio CRUD
3. P2: Market data pipeline (IN PROGRESS) - Kafka, TimescaleDB integration
4. P3: Web dashboard - Real-time UI, WebSocket integration
5. P4-5: AI agent service - LLM insights and recommendations

### Known Issues & TODOs

From `docs/draft/springboot_work_log.md`:
- [ ] Testcontainers setup for integration tests
- [ ] OAuth2/JWT authentication
- [ ] Portfolio/Asset/Notification services
- [ ] WebSocket Gateway implementation
- [ ] Kafka integration
- [ ] Monitoring (Prometheus/Grafana)

## Key Files to Reference

| File | Purpose |
|------|---------|
| `AGENTS.md` | Quick reference for agents (condensed version) |
| `README.md` | Setup and usage instructions |
| `docs/01_project_summary.md` | Project goals, KPIs, risks |
| `docs/02_core_architecture.md` | System architecture, tech stack |
| `docs/03_marketdata_pipeline.md` | Market data flow details |
| `docs/05_development_phases.md` | Development roadmap |
| `docs/draft/springboot_work_log.md` | Spring Boot implementation log |
| `docker-compose.yml` | Infrastructure configuration |
| `apps/core-api/build.gradle` | Java dependencies |
| `services/market-data/pyproject.toml` | Python dependencies |

## Environment Variables

Required in `.env` file (root directory):

```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=portrally
DB_USER=portrally
DB_PASSWORD=<password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# API
API_PORT=8080

# Market Data
PROVIDER=upbit              # upbit, binance, kis
SYMBOLS=KRW-BTC,KRW-ETH    # Comma-separated symbols
REDIS_CHANNEL=quotes       # Redis Pub/Sub channel

# KIS (Korean Investment & Securities) - Optional
KIS_APP_KEY=<key>
KIS_APP_SECRET=<secret>
KIS_ACCOUNT=<account>
KIS_APPROVAL_KEY=<key>
```

## Questions & Troubleshooting

### How do I...?

**Run just the market data service?**
```bash
cd services/market-data
source .venv/bin/activate
export PYTHONPATH=src
uv run -m quote_pipeline.main --provider upbit --symbols KRW-BTC
```

**Add a new database column?**
Create a new Flyway migration file (never modify existing ones):
```sql
-- V9__add_user_avatar.sql
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
```

**Check if WebSocket is receiving data?**
```bash
redis-cli -u redis://localhost:6379/0 SUBSCRIBE quotes
# Should see messages like: message, quotes, {"symbol":"KRW-BTC",...}
```

**Access Swagger UI?**
http://localhost:8080/swagger-ui.html (after starting core-api)

**Run tests?**
```bash
# Python
cd services/market-data && uv run -m pytest tests/

# Java
cd apps/core-api && ./gradlew test
```

## Contact & Resources

- Issue Tracking: Use descriptive commit messages and reference issue numbers if applicable
- Documentation: Keep `docs/` folder updated with architectural changes
- Code Review: Focus on reactive programming patterns, security, and test coverage

---

This guide is maintained to help AI assistants understand and work effectively with the PortRally codebase. Update this file when making significant architectural or workflow changes.
