"""
코스피주식종목코드(kospi_code.mst) 정제 파이썬 파일
- Source: https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip
- Output: data/kospi_master/kospi_code_YYMMDD.csv
"""

import ssl
import zipfile
import urllib.request
from pathlib import Path
from datetime import datetime

import pandas as pd

RUN_DATE = datetime.now().strftime("%y%m%d")

# 데이터 저장 경로를 market-data/data/kospi_master 로 고정
base_dir = Path(__file__).resolve().parents[3] / "data" / "kospi_master"
base_dir.mkdir(parents=True, exist_ok=True)


def kospi_master_download(base_dir: Path, verbose: bool = False) -> tuple[Path, Path]:
    """
    kospi_code.mst.zip 다운로드 후 압축 해제
    반환:
      - zip_path: 다운로드된 zip 경로
      - mst_path: 압축 해제된 mst 경로
    """
    ssl._create_default_https_context = ssl._create_unverified_context

    zip_path = base_dir / "kospi_code.mst.zip"
    mst_path = base_dir / "kospi_code.mst"

    urllib.request.urlretrieve(
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        zip_path,
    )
    if verbose:
        print(f"Downloaded... {zip_path.name}")

    with zipfile.ZipFile(zip_path) as zf:
        if verbose:
            print(f"Extracting... {zip_path.name}")
        zf.extractall(base_dir)

    return zip_path, mst_path


def get_kospi_master_dataframe(base_dir: Path) -> pd.DataFrame:
    """
    kospi_code.mst -> DataFrame 변환
    원본 포맷 특성상 part1/part2 임시 파일을 생성해 파싱 (원본 로직 유지)
    """
    mst_path = base_dir / "kospi_code.mst"
    tmp_fil1 = base_dir / "kospi_code_part1.tmp"
    tmp_fil2 = base_dir / "kospi_code_part2.tmp"

    # 1) mst를 part1/part2로 분해
    with open(tmp_fil1, mode="w", encoding="cp949") as wf1, open(
        tmp_fil2, mode="w", encoding="cp949"
    ) as wf2:
        with open(mst_path, mode="r", encoding="cp949") as f:
            for row in f:
                rf1 = row[0 : len(row) - 228]
                rf1_1 = rf1[0:9].rstrip()
                rf1_2 = rf1[9:21].rstrip()
                rf1_3 = rf1[21:].strip()
                wf1.write(rf1_1 + "," + rf1_2 + "," + rf1_3 + "\n")

                rf2 = row[-228:]
                wf2.write(rf2)

    # 2) part1 로드
    part1_columns = ["단축코드", "표준코드", "한글명"]
    df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding="cp949")

    # 3) part2 로드 (고정폭)
    field_specs = [
        2, 1, 4, 4, 4,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 9, 5, 5, 1,
        1, 1, 2, 1, 1,
        1, 2, 2, 2, 3,
        1, 3, 12, 12, 8,
        15, 21, 2, 7, 1,
        1, 1, 1, 1, 9,
        9, 9, 5, 9, 8,
        9, 3, 1, 1, 1
    ]

    part2_columns = [
        "그룹코드", "시가총액규모", "지수업종대분류", "지수업종중분류", "지수업종소분류",
        "제조업", "저유동성", "지배구조지수종목", "KOSPI200섹터업종", "KOSPI100",
        "KOSPI50", "KRX", "ETP", "ELW발행", "KRX100",
        "KRX자동차", "KRX반도체", "KRX바이오", "KRX은행", "SPAC",
        "KRX에너지화학", "KRX철강", "단기과열", "KRX미디어통신", "KRX건설",
        "Non1", "KRX증권", "KRX선박", "KRX섹터_보험", "KRX섹터_운송",
        "SRI", "기준가", "매매수량단위", "시간외수량단위", "거래정지",
        "정리매매", "관리종목", "시장경고", "경고예고", "불성실공시",
        "우회상장", "락구분", "액면변경", "증자구분", "증거금비율",
        "신용가능", "신용기간", "전일거래량", "액면가", "상장일자",
        "상장주수", "자본금", "결산월", "공모가", "우선주",
        "공매도과열", "이상급등", "KRX300", "KOSPI", "매출액",
        "영업이익", "경상이익", "당기순이익", "ROE", "기준년월",
        "시가총액", "그룹사코드", "회사신용한도초과", "담보대출가능", "대주가능",
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


def run_kospi_export(base_dir: Path, verbose: bool = True) -> Path:
    """
    다운로드 -> 파싱 -> CSV 저장 -> 원본(zip/mst) 정리
    """
    zip_path = None
    mst_path = None

    try:
        zip_path, mst_path = kospi_master_download(base_dir, verbose=verbose)

        if verbose:
            print(f"Parsing... {mst_path.name}")
        df = get_kospi_master_dataframe(base_dir)

        out_path = base_dir / f"kospi_code_{RUN_DATE}.csv"
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
    out = run_kospi_export(base_dir, verbose=True)
    print(f"Done: {out}")
