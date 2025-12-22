import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from quote_pipeline.db import get_db
from quote_pipeline.master_loader.market.kosdaq_master import (
    base_dir as KOSDAQ_MASTER_DIR,
    run_kosdaq_export,
)
from quote_pipeline.master_loader.market.kospi_master import (
    base_dir as KOSPI_MASTER_DIR,
    run_kospi_export,
)
from quote_pipeline.master_loader.market.overseas_master import (
    base_dir as OVERSEAS_MASTER_DIR,
    run_overseas_export,
)

logger = logging.getLogger(__name__)


def _safe_str(val) -> str:
    """NaN/None을 빈 문자열로, 그 외는 strip된 문자열로 반환."""
    if pd.isna(val):
        return ""
    return str(val).strip()

def _get_data_dir() -> Path:
    py_path = os.environ.get("PYTHONPATH", "src")
    root = py_path.split(os.pathsep)[0] or "src"
    return Path(root).resolve() / ".." / "data"


# 데이터 디렉토리 경로 (PYTHONPATH 기준)
DATA_DIR = _get_data_dir()

# 테이블 생성 DDL
CREATE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS securities_master (
  id           BIGSERIAL PRIMARY KEY,

  national     TEXT NOT NULL,
  market       TEXT NOT NULL,
  symbol       TEXT NOT NULL,

  isin         TEXT NULL,
  name_ko      TEXT NULL,
  name_en      TEXT NULL,

  asset_type   TEXT NULL,
  currency     TEXT NOT NULL,

  sector_scheme TEXT NULL,
  sector_tags  TEXT[] NULL,

  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_securities_master UNIQUE (national, market, symbol),

  CONSTRAINT ck_asset_type CHECK (
    asset_type IS NULL OR asset_type IN ('STOCK','ETF','ETN','INDEX','WARRANT','OTHER')
  )
);

CREATE INDEX IF NOT EXISTS idx_securities_master_isin ON securities_master(isin);
CREATE INDEX IF NOT EXISTS idx_securities_master_name_ko ON securities_master(name_ko);
CREATE INDEX IF NOT EXISTS idx_securities_master_name_en ON securities_master(name_en);
"""

# UPSERT 쿼리
UPSERT_SQL = """
INSERT INTO securities_master (national, market, symbol, isin, name_ko, name_en, asset_type, currency)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (national, market, symbol)
DO UPDATE SET
  isin = EXCLUDED.isin,
  name_ko = EXCLUDED.name_ko,
  name_en = EXCLUDED.name_en,
  asset_type = EXCLUDED.asset_type,
  currency = EXCLUDED.currency,
  updated_at = NOW()
"""

# 동일 국가/마켓 범위에서 CSV에 없는 심볼을 제거
DELETE_MISSING_SQL = """
DELETE FROM securities_master
WHERE national = $1
  AND market = $2
  AND NOT (symbol = ANY($3))
"""


class MasterLoader:
    """종목 마스터 CSV 파일을 DB에 로드하는 클래스."""

    def __init__(self) -> None:
        self.db = get_db()

    async def check_connection(self) -> bool:
        """DB 연결 상태를 확인하고 로그를 출력한다."""
        try:
            await self.db.connect()
            version = await self.db.fetchval("SELECT version()")
            logger.info("[MasterLoader] DB 연결 성공")
            logger.info("[MasterLoader] PostgreSQL version: %s", version)

            db_name = await self.db.fetchval("SELECT current_database()")
            db_user = await self.db.fetchval("SELECT current_user")
            logger.info("[MasterLoader] Database: %s, User: %s", db_name, db_user)
            return True
        except Exception as e:
            logger.error("[MasterLoader] DB 연결 실패: %s", e)
            return False

    async def _table_exists(self) -> bool:
        """securities_master 테이블 존재 여부 확인."""
        result = await self.db.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'securities_master'
            )
        """)
        return result

    async def create_table(self, force: bool = False) -> bool:
        """securities_master 테이블 생성. 이미 존재하면 스킵."""
        await self.db.connect()

        if not force and await self._table_exists():
            logger.info("[MasterLoader] 테이블이 이미 존재합니다. 스킵.")
            return False

        await self.db.execute(CREATE_TABLE_DDL)
        logger.info("[MasterLoader] 테이블 생성 완료")
        return True

    def _refresh_master_files(self) -> None:
        """마켓별 마스터 CSV를 최신으로 갱신합니다."""
        logger.info("[MasterLoader] Refreshing master CSVs (KOSPI/KOSDAQ/OVERSEAS)")
        run_kospi_export(KOSPI_MASTER_DIR, verbose=True)
        run_kosdaq_export(KOSDAQ_MASTER_DIR, verbose=True)
        run_overseas_export(OVERSEAS_MASTER_DIR, verbose=True)
        logger.info("[MasterLoader] Master CSV refresh complete")

    def _find_latest_csv(self, directory: Path, prefix: str) -> Optional[Path]:
        """YYMMDD가 가장 최신인 CSV 파일을 찾는다."""
        pattern = re.compile(rf"{prefix}_(\d{{6}})\.csv$")
        candidates = []

        if not directory.exists():
            logger.warning("[MasterLoader] 디렉토리 없음: %s", directory)
            return None

        for f in directory.iterdir():
            match = pattern.match(f.name)
            if match:
                date_str = match.group(1)
                candidates.append((date_str, f))

        if not candidates:
            logger.warning("[MasterLoader] %s 패턴의 CSV 파일 없음: %s", prefix, directory)
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        latest = candidates[0][1]
        logger.info("[MasterLoader] 최신 파일: %s", latest.name)
        return latest

    def _parse_kospi_csv(self, filepath: Path) -> list[tuple]:
        """KOSPI CSV를 파싱하여 DB 레코드 튜플 리스트 반환."""
        df = pd.read_csv(filepath, dtype=str)
        records = []

        for _, row in df.iterrows():
            symbol = _safe_str(row.get("단축코드"))
            if not symbol:
                continue

            isin = _safe_str(row.get("표준코드")) or None
            name_ko = _safe_str(row.get("한글명")) or None

            # asset_type 결정
            etp = _safe_str(row.get("ETP"))
            asset_type = "ETF" if etp else "STOCK"

            records.append((
                "KR",       # national
                "KOSPI",    # market
                symbol,
                isin,
                name_ko,
                None,       # name_en
                asset_type,
                "KRW",      # currency
            ))

        return records

    def _parse_kosdaq_csv(self, filepath: Path) -> list[tuple]:
        """KOSDAQ CSV를 파싱하여 DB 레코드 튜플 리스트 반환."""
        df = pd.read_csv(filepath, dtype=str)
        records = []

        for _, row in df.iterrows():
            symbol = _safe_str(row.get("단축코드"))
            if not symbol:
                continue

            isin = _safe_str(row.get("표준코드")) or None
            name_ko = _safe_str(row.get("한글종목명")) or None

            # asset_type 결정
            etp = _safe_str(row.get("ETP 상품구분코드"))
            asset_type = "ETF" if etp else "STOCK"

            records.append((
                "KR",       # national
                "KOSDAQ",   # market
                symbol,
                isin,
                name_ko,
                None,       # name_en
                asset_type,
                "KRW",      # currency
            ))

        return records

    def _parse_overseas_csv(self, filepath: Path) -> list[tuple]:
        """해외 종목 CSV를 파싱하여 DB 레코드 튜플 리스트 반환."""
        df = pd.read_csv(filepath, dtype=str)
        records = []

        # Security type 매핑: 1=INDEX, 2=STOCK, 3=ETF, 4=WARRANT
        sec_type_map = {
            "1": "INDEX",
            "2": "STOCK",
            "3": "ETF",
            "4": "WARRANT",
        }

        for _, row in df.iterrows():
            symbol = _safe_str(row.get("Symbol"))
            if not symbol:
                continue

            national = _safe_str(row.get("National code")) or "US"
            market = _safe_str(row.get("Exchange code")) or "NAS"
            name_ko = _safe_str(row.get("Korea name")) or None
            name_en = _safe_str(row.get("English name")) or None
            currency = _safe_str(row.get("currency")) or "USD"

            # Security type
            sec_type_raw = _safe_str(row.get("Security type(1:Index,2:Stock,3:ETP(ETF),4:Warrant)"))
            asset_type = sec_type_map.get(sec_type_raw, "OTHER")

            records.append((
                national,
                market,
                symbol,
                None,       # isin (해외는 없음)
                name_ko,
                name_en,
                asset_type,
                currency,
            ))

        return records

    async def load_all(self, refresh_master: bool = True) -> dict[str, int]:
        """모든 CSV 파일을 읽어 DB에 저장."""
        if refresh_master:
            self._refresh_master_files()
        await self.create_table()

        result = {"kospi": 0, "kosdaq": 0, "overseas": 0}

        # 데이터 디렉토리 준비
        data_dirs = [
            DATA_DIR / "kospi_master",
            DATA_DIR / "kosdaq_master",
            DATA_DIR / "overseas_master",
        ]
        for d in data_dirs:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                logger.info("[MasterLoader] Created data dir: %s", d)

        # KOSPI
        kospi_csv = self._find_latest_csv(DATA_DIR / "kospi_master", "kospi_code")
        if kospi_csv:
            records = self._parse_kospi_csv(kospi_csv)
            await self._upsert_records(records)
            # KOSPI는 단일 마켓이므로 같은 범위에서 CSV 누락 종목을 삭제
            await self._delete_missing_records("KR", "KOSPI", records)
            result["kospi"] = len(records)
            logger.info("[MasterLoader] KOSPI 로드 완료: %d건", len(records))

        # KOSDAQ
        kosdaq_csv = self._find_latest_csv(DATA_DIR / "kosdaq_master", "kosdaq_code")
        if kosdaq_csv:
            records = self._parse_kosdaq_csv(kosdaq_csv)
            await self._upsert_records(records)
            # KOSDAQ도 단일 마켓 범위에서 CSV 누락 종목을 삭제
            await self._delete_missing_records("KR", "KOSDAQ", records)
            result["kosdaq"] = len(records)
            logger.info("[MasterLoader] KOSDAQ 로드 완료: %d건", len(records))

        # OVERSEAS
        overseas_csv = self._find_latest_csv(DATA_DIR / "overseas_master", "overseas_all_stock_code")
        if overseas_csv:
            records = self._parse_overseas_csv(overseas_csv)
            await self._upsert_records(records)
            # 해외는 국가/거래소 조합이 다양하므로 그룹별로 삭제
            await self._delete_missing_overseas_records(records)
            result["overseas"] = len(records)
            logger.info("[MasterLoader] OVERSEAS 로드 완료: %d건", len(records))

        total = sum(result.values())
        logger.info("[MasterLoader] 전체 로드 완료: %d건", total)
        return result

    async def _upsert_records(self, records: list[tuple]) -> None:
        """레코드를 DB에 UPSERT."""
        if not records:
            return

        async with self.db.acquire() as conn:
            await conn.executemany(UPSERT_SQL, records)

    async def _delete_missing_records(
        self,
        national: str,
        market: str,
        records: list[tuple],
    ) -> None:
        """CSV에 없는 종목을 동일 국가/마켓 범위에서 삭제."""
        # 레코드의 3번째 값이 symbol이며, 빈 심볼은 제외
        symbols = [r[2] for r in records if r[2]]
        if not symbols:
            # 심볼이 없으면 전체 삭제 위험이 있어 스킵
            logger.warning(
                "[MasterLoader] 삭제 스킵: %s/%s CSV에 심볼이 없습니다.",
                national,
                market,
            )
            return

        async with self.db.acquire() as conn:
            # DB에 남아있는 동일 국가/마켓 중 CSV에 없는 심볼만 제거
            await conn.execute(DELETE_MISSING_SQL, national, market, symbols)

    async def _delete_missing_overseas_records(self, records: list[tuple]) -> None:
        """해외 CSV 기준으로 국가/거래소별 삭제."""
        # (national, market)별로 심볼을 모아 범위 제한 삭제를 수행
        symbols_by_key: dict[tuple[str, str], set[str]] = {}
        for record in records:
            national, market, symbol = record[0], record[1], record[2]
            if not symbol:
                continue
            symbols_by_key.setdefault((national, market), set()).add(symbol)

        async with self.db.acquire() as conn:
            # 국가/거래소별로 CSV 누락 종목만 삭제
            for (national, market), symbols in symbols_by_key.items():
                await conn.execute(DELETE_MISSING_SQL, national, market, list(symbols))

    async def close(self) -> None:
        """DB 연결 종료."""
        await self.db.close()


async def main() -> None:
    """엔트리포인트."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    loader = MasterLoader()

    try:
        if not await loader.check_connection():
            return

        result = await loader.load_all()
        logger.info("[MasterLoader] 결과: %s", result)
    finally:
        await loader.close()


if __name__ == "__main__":
    asyncio.run(main())
