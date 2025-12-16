import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from asyncpg import Pool

# 환경변수 기본값 (docker compose 설정 기준)
DEFAULT_DB_HOST = "postgres"
DEFAULT_DB_PORT = 5432
DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PASSWORD = "postgres"
DEFAULT_DB_NAME = "port_rally"


class Database:
    """PostgreSQL 비동기 연결 관리 클래스."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        self.host = host or os.getenv("DB_HOST", DEFAULT_DB_HOST)
        self.port = port or int(os.getenv("DB_PORT", DEFAULT_DB_PORT))
        self.user = user or os.getenv("DB_USER", DEFAULT_DB_USER)
        self.password = password or os.getenv("DB_PASSWORD", DEFAULT_DB_PASSWORD)
        self.database = database or os.getenv("DB_NAME", DEFAULT_DB_NAME)
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[Pool] = None

    @property
    def dsn(self) -> str:
        """PostgreSQL DSN 문자열 반환."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    async def connect(self) -> Pool:
        """커넥션 풀 생성 및 반환."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=self.min_size,
                max_size=self.max_size,
            )
        return self._pool

    async def close(self) -> None:
        """커넥션 풀 종료."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def acquire(self):
        """커넥션 획득 컨텍스트 매니저."""
        pool = await self.connect()
        async with pool.acquire() as conn:
            yield conn

    async def execute(self, query: str, *args) -> str:
        """단일 쿼리 실행."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """쿼리 실행 및 모든 행 반환."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """쿼리 실행 및 단일 행 반환."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """쿼리 실행 및 단일 값 반환."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args: list) -> None:
        """여러 행 일괄 삽입."""
        async with self.acquire() as conn:
            await conn.executemany(query, args)

    async def copy_records_to_table(
        self, table_name: str, records: list, columns: list[str]
    ) -> str:
        """COPY 프로토콜을 사용한 대량 삽입 (가장 빠름)."""
        async with self.acquire() as conn:
            return await conn.copy_records_to_table(
                table_name, records=records, columns=columns
            )


# 싱글톤 인스턴스
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Database 싱글톤 인스턴스 반환."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
