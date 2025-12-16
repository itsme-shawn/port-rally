종목 마스터 저장 흐름


- services/market-data/quote_pipeline/code_master 에서 각 kospi/kosdaq/overseas 의 master csv 를 수집 후 market-data/data/ 경로에 저장
- 각각 kospi_code_YYMMDD.csv , kosdaq_code_YYMMDD.csv, overseas_all_stock_code_YYMMDD.csv 파일 세 개가 쌓이는데 YYMMDD 가 가장 최신인 파일을 읽어서 DB 에 저장
- 각 csv 의 스키마는 다르고, 각 csv 를 적절히 파싱해서 아래의 DB 에 저장
- 종목마스터 DB 스키마 (mvp ver)
```
테이블명 : securities_master

CREATE TABLE securities_master (
  id           BIGSERIAL PRIMARY KEY,

  national     TEXT NOT NULL,   -- KR, US
  market       TEXT NOT NULL,   -- KOSPI, KOSDAQ, NAS, NYS ...
  symbol       TEXT NOT NULL,   -- 단축코드 / Symbol

  isin         TEXT NULL,       -- KR... / (없으면 NULL)
  name_ko      TEXT NULL,
  name_en      TEXT NULL,

  asset_type   TEXT NULL,       -- STOCK/ETF/ETN/INDEX/WARRANT/OTHER
  currency     TEXT NOT NULL,   -- KRW/USD...

  sector_scheme TEXT NULL,      -- optional but recommended
  sector_tags  TEXT[] NULL,     -- ['Technology', 'Semiconductor', 'Memory']

  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_securities_master UNIQUE (national, market, symbol),

  CONSTRAINT ck_asset_type CHECK (
    asset_type IS NULL OR asset_type IN ('STOCK','ETF','ETN','INDEX','WARRANT','OTHER')
  )
);

CREATE INDEX idx_securities_master_isin ON securities_master(isin);
CREATE INDEX idx_securities_master_name_ko ON securities_master(name_ko);
CREATE INDEX idx_securities_master_name_en ON securities_master(name_en);
```