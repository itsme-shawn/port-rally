# https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/overseas_stock_code.py

'''해외주식종목코드 정제 파이썬 파일
미국 : nasmst.cod, nysmst.cod, amsmst.cod, 
중국 : shsmst.cod, shimst.cod, szsmst.cod, szimst.cod, 
일본 : tsemst.cod, 
홍콩 : hksmst.cod, 
베트남 : hnxmst.cod, hsxmst.cod'''

'''
※ 유의사항 ※
실행 환경 혹은 원본 파일의 칼럼 수의 변경으로 간혹 정제코드 파일(overseas_stock_code.py)이 실행되지 않을 수 있습니다.
해당 경우, URL에 아래 링크를 복사+붙여넣기 하여 원본 파일을 다운로드하시기 바랍니다.
. https://new.real.download.dws.co.kr/common/master/{val}mst.cod.zip
. {val} 자리에 원하시는 시장코드를 넣어주세요.
. 'nas','nys','ams','shs','shi','szs','szi','tse','hks','hnx','hsx'
. 순서대로 나스닥, 뉴욕, 아멕스, 상해, 상해지수, 심천, 심천지수, 도쿄, 홍콩, 하노이, 호치민
'''

import pandas as pd
import urllib.request
import ssl
import zipfile
import os
from pathlib import Path
from datetime import datetime

RUN_DATE = datetime.now().strftime("%y%m%d")

# 데이터 저장 경로를 market-data/data/overseas_master 로 고정
base_dir = Path(__file__).resolve().parents[3] / "data" / "overseas_master"
base_dir.mkdir(parents=True, exist_ok=True)

def get_overseas_master_dataframe(base_dir, mkt):
    ssl._create_default_https_context = ssl._create_unverified_context

    zip_path = base_dir / f"{mkt}mst.cod.zip"
    cod_path = base_dir / f"{mkt.upper()}MST.COD"

    try:
        # 1. ZIP 다운로드
        urllib.request.urlretrieve(
            f"https://new.real.download.dws.co.kr/common/master/{mkt}mst.cod.zip",
            zip_path,
        )
        print(f"Downloaded... {zip_path.name}")

        # 2. 압축 해제
        with zipfile.ZipFile(zip_path) as overseas_zip:
            print(f"Extracting... {zip_path.name}")
            overseas_zip.extractall(base_dir)

        columns = [
            'National code', 'Exchange id', 'Exchange code', 'Exchange name',
            'Symbol', 'realtime symbol', 'Korea name', 'English name',
            'Security type(1:Index,2:Stock,3:ETP(ETF),4:Warrant)',
            'currency', 'float position', 'data type', 'base price',
            'Bid order size', 'Ask order size',
            'market start time(HHMM)', 'market end time(HHMM)',
            'DR 여부(Y/N)', 'DR 국가코드', '업종분류코드',
            '지수구성종목 존재 여부(0:구성종목없음,1:구성종목있음)',
            'Tick size Type',
            '구분코드(001:ETF,002:ETN,003:ETC,004:Others,005:VIX Underlying ETF,006:VIX Underlying ETN)',
            'Tick size type 상세'
        ]

        print(f"Parsing... {cod_path.name}")
        df = pd.read_table(cod_path, sep='\t', encoding='cp949')
        df.columns = columns

        # 3. CSV 저장
        csv_path = base_dir / f"{mkt}_code_{RUN_DATE}.csv"
        df.to_csv(csv_path, index=False)

        return df

    finally:
        # 4. 원본 파일 정리
        if cod_path.exists():
            cod_path.unlink()
        if zip_path.exists():
            zip_path.unlink()



if __name__ == "__main__":
    # 순서대로 나스닥, 뉴욕, 아멕스, 상해, 상해지수, 심천, 심천지수, 도쿄, 홍콩, 하노이, 호치민
    markets = ['nas','nys','ams','shs','shi','szs','szi','tse','hks','hnx','hsx'] 

    DF=pd.DataFrame()
    for mkt in markets:
        temp = get_overseas_master_dataframe(base_dir,mkt)
        DF = pd.concat([DF,temp],axis=0)
    all_csv_path = base_dir / f"overseas_all_stock_code_{RUN_DATE}.csv"
    print(f"Saving... {all_csv_path.name}")
    DF.to_csv(all_csv_path, index=False) # 전체 통합본 저장

    print("Done")