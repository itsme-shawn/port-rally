"""KIS domestic quote DTO - KIS 국내주식 실시간 체결가 데이터 전송 객체."""

from dataclasses import dataclass


@dataclass
class KisDomesticQuoteDTO:
    """
    KIS 국내주식 실시간 체결가(통합) (H0UNCNT0) DTO.

    데이터 형식: 0|H0UNCNT0|001|005930^191053^108000^...
    필드는 ^ 구분자로 분리됩니다.

    참고: https://apiportal.koreainvestment.com/apiservice/apiservice-domestic-stock-real
    """

    # 기본 정보
    MKSC_SHRN_ISCD: str
    """유가증권 단축 종목코드 (예: 005930)"""

    STCK_CNTG_HOUR: str
    """주식 체결 시간 (HHMMSS)"""

    STCK_PRPR: str
    """주식 현재가"""

    PRDY_VRSS_SIGN: str
    """전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)"""

    PRDY_VRSS: str
    """전일 대비"""

    PRDY_CTRT: str
    """전일 대비율 (%)"""

    WGHN_AVRG_STCK_PRC: str
    """가중 평균 주식 가격"""

    STCK_OPRC: str
    """주식 시가"""

    STCK_HGPR: str
    """주식 최고가"""

    STCK_LWPR: str
    """주식 최저가"""

    ASKP1: str
    """매도호가1"""

    BIDP1: str
    """매수호가1"""

    CNTG_VOL: str
    """체결 거래량"""

    ACML_VOL: str
    """누적 거래량"""

    ACML_TR_PBMN: str
    """누적 거래 대금"""

    SELN_CNTG_CSNU: str
    """매도 체결 건수"""

    SHNU_CNTG_CSNU: str
    """매수 체결 건수"""

    NTBY_CNTG_CSNU: str
    """순매수 체결 건수"""

    CTTR: str
    """체결강도"""

    SELN_CNTG_SMTN: str
    """총 매도 수량"""

    SHNU_CNTG_SMTN: str
    """총 매수 수량"""

    CCLD_DVSN: str
    """체결구분 (1:매수, 3:장전, 5:매도)"""

    SHNU_RATE: str
    """매수비율"""

    PRDY_VOL_VRSS_ACML_VOL_RATE: str
    """전일 거래량 대비 등락율"""

    OPRC_HOUR: str
    """시가 시간"""

    OPRC_VRSS_PRPR_SIGN: str
    """시가대비구분"""

    OPRC_VRSS_PRPR: str
    """시가대비"""

    HGPR_HOUR: str
    """최고가 시간"""

    HGPR_VRSS_PRPR_SIGN: str
    """고가대비구분"""

    HGPR_VRSS_PRPR: str
    """고가대비"""

    LWPR_HOUR: str
    """최저가 시간"""

    LWPR_VRSS_PRPR_SIGN: str
    """저가대비구분"""

    LWPR_VRSS_PRPR: str
    """저가대비"""

    BSOP_DATE: str
    """영업 일자 (YYYYMMDD)"""

    NEW_MKOP_CLS_CODE: str
    """신 장운영 구분 코드"""

    TRHT_YN: str
    """거래정지 여부 (Y/N)"""

    ASKP_RSQN1: str
    """매도호가 잔량1"""

    BIDP_RSQN1: str
    """매수호가 잔량1"""

    TOTAL_ASKP_RSQN: str
    """총 매도호가 잔량"""

    TOTAL_BIDP_RSQN: str
    """총 매수호가 잔량"""

    VOL_TNRT: str
    """거래량 회전율"""

    PRDY_SMNS_HOUR_ACML_VOL: str
    """전일 동시간 누적 거래량"""

    PRDY_SMNS_HOUR_ACML_VOL_RATE: str
    """전일 동시간 누적 거래량 비율"""

    HOUR_CLS_CODE: str
    """시간 구분 코드"""

    MRKT_TRTM_CLS_CODE: str
    """임의종료구분코드"""

    VI_STND_PRC: str
    """정적VI발동기준가"""

    @property
    def symbol(self) -> str:
        """종목코드 반환."""
        return self.MKSC_SHRN_ISCD

    @property
    def market(self) -> str:
        """마켓 코드 반환 (KOSPI/KOSDAQ 구분은 추후 구현)."""
        # 종목코드 첫자리로 대략적인 구분 가능
        # 0~4: KOSPI, 5~9: KOSDAQ (대략적)
        # 정확한 구분은 종목마스터 DB 조회 필요
        return "KOSPI"  # 기본값
