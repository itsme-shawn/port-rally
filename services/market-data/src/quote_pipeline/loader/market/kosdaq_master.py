"""
코스닥주식종목코드(kosdaq_code.mst) 정제 파이썬 파일
- Source: https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip
- Output: data/kosdaq_master/kosdaq_code_YYMMDD.csv
"""

import os
import ssl
import zipfile
import urllib.request
from pathlib import Path
from datetime import datetime

import pandas as pd

RUN_DATE = datetime.now().strftime("%y%m%d")

def _get_data_dir() -> Path:
    py_path = os.environ.get("PYTHONPATH", "src")
    root = py_path.split(os.pathsep)[0] or "src"
    return Path(root).resolve() / ".." / "data"


# 데이터 저장 경로 (PYTHONPATH 기준)
base_dir = _get_data_dir() / "kosdaq_master"
base_dir.mkdir(parents=True, exist_ok=True)


def kosdaq_master_download(base_dir: Path, verbose: bool = False) -> tuple[Path, Path]:
    """
    kosdaq_code.mst.zip 다운로드 후 압축 해제
    반환:
      - zip_path: 다운로드된 zip 경로
      - mst_path: 압축 해제된 mst 경로
    """
    ssl._create_default_https_context = ssl._create_unverified_context

    zip_path = base_dir / "kosdaq_code.mst.zip"
    mst_path = base_dir / "kosdaq_code.mst"

    urllib.request.urlretrieve(
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
        zip_path,
    )
    if verbose:
        print(f"Downloaded... {zip_path.name}")

    with zipfile.ZipFile(zip_path) as zf:
        if verbose:
            print(f"Extracting... {zip_path.name}")
        zf.extractall(base_dir)

    return zip_path, mst_path


def get_kosdaq_master_dataframe(base_dir: Path) -> pd.DataFrame:
    """
    kosdaq_code.mst -> DataFrame 변환
    원본 포맷 특성상 part1/part2 임시 파일을 생성해 파싱 (원본 로직 유지)
    """
    mst_path = base_dir / "kosdaq_code.mst"
    tmp_fil1 = base_dir / "kosdaq_code_part1.tmp"
    tmp_fil2 = base_dir / "kosdaq_code_part2.tmp"

    # 1) mst를 part1/part2로 분해
    with open(tmp_fil1, mode="w", encoding="cp949") as wf1, open(
        tmp_fil2, mode="w", encoding="cp949"
    ) as wf2:
        with open(mst_path, mode="r", encoding="cp949") as f:
            for row in f:
                rf1 = row[0 : len(row) - 222]
                rf1_1 = rf1[0:9].rstrip()
                rf1_2 = rf1[9:21].rstrip()
                rf1_3 = rf1[21:].strip()
                wf1.write(rf1_1 + "," + rf1_2 + "," + rf1_3 + "\n")

                rf2 = row[-222:]
                wf2.write(rf2)

    # 2) part1 로드
    part1_columns = ["단축코드", "표준코드", "한글종목명"]
    df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding="cp949")

    # 3) part2 로드 (고정폭)
    field_specs = [
        2, 1,
        4, 4, 4, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 9,
        5, 5, 1, 1, 1,
        2, 1, 1, 1, 2,
        2, 2, 3, 1, 3,
        12, 12, 8, 15, 21,
        2, 7, 1, 1, 1,
        1, 9, 9, 9, 5,
        9, 8, 9, 3, 1,
        1, 1
    ]

    part2_columns = [
        "증권그룹구분코드", "시가총액 규모 구분 코드 유가",
        "지수업종 대분류 코드", "지수 업종 중분류 코드", "지수업종 소분류 코드",
        "벤처기업 여부 (Y/N)", "저유동성종목 여부", "KRX 종목 여부", "ETP 상품구분코드",
        "KRX100 종목 여부 (Y/N)", "KRX 자동차 여부", "KRX 반도체 여부", "KRX 바이오 여부",
        "KRX 은행 여부", "기업인수목적회사여부", "KRX 에너지 화학 여부", "KRX 철강 여부",
        "단기과열종목구분코드", "KRX 미디어 통신 여부", "KRX 건설 여부",
        "(코스닥)투자주의환기종목여부", "KRX 증권 구분", "KRX 선박 구분",
        "KRX섹터지수 보험여부", "KRX섹터지수 운송여부", "KOSDAQ150지수여부 (Y,N)",
        "주식 기준가", "정규 시장 매매 수량 단위", "시간외 시장 매매 수량 단위",
        "거래정지 여부", "정리매매 여부", "관리 종목 여부", "시장 경고 구분 코드",
        "시장 경고위험 예고 여부", "불성실 공시 여부", "우회 상장 여부", "락구분 코드",
        "액면가 변경 구분 코드", "증자 구분 코드", "증거금 비율", "신용주문 가능 여부",
        "신용기간", "전일 거래량", "주식 액면가", "주식 상장 일자", "상장 주수(천)",
        "자본금", "결산 월", "공모 가격", "우선주 구분 코드", "공매도과열종목여부",
        "이상급등종목여부", "KRX300 종목 여부 (Y/N)", "매출액", "영업이익", "경상이익",
        "단기순이익", "ROE(자기자본이익률)", "기준년월", "전일기준 시가총액 (억)",
        "그룹사 코드", "회사신용한도초과여부", "담보대출가능여부", "대주가능여부"
    ]

    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns)

    # 4) 병합
    df = pd.merge(df1, df2, how="outer", left_index=True, right_index=True)

    # 5) 임시 파일 정리
    if tmp_fil1.exists():
        tmp_fil1.unlink()
    if tmp_fil2.exists():
        tmp_fil2.unlink()

    return df


def run_kosdaq_export(base_dir: Path, verbose: bool = True) -> Path:
    """
    다운로드 -> 파싱 -> CSV 저장 -> 원본(zip/mst) 정리
    """
    zip_path = None
    mst_path = None

    try:
        zip_path, mst_path = kosdaq_master_download(base_dir, verbose=verbose)

        if verbose:
            print(f"Parsing... {mst_path.name}")
        df = get_kosdaq_master_dataframe(base_dir)

        out_path = base_dir / f"kosdaq_code_{RUN_DATE}.csv"
        if verbose:
            print(f"Saving... {out_path.name}")
        df.to_csv(out_path, index=False)

        return out_path

    finally:
        # 원본 파일 정리 (zip/mst)
        if mst_path and mst_path.exists():
            mst_path.unlink()
        if zip_path and zip_path.exists():
            zip_path.unlink()


if __name__ == "__main__":
    out = run_kosdaq_export(base_dir, verbose=True)
    print(f"Done: {out}")
