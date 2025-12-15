"""KIS overseas quote DTO - KIS 해외주식 실시간 체결가 데이터 전송 객체."""

from dataclasses import dataclass


@dataclass
class KisOverseasQuoteDTO:
    """
    KIS 해외주식 실시간 체결가 (HDFSCNT0) raw data.

    데이터 형식: "0|HDFSCNT0|001|{data}"
    data 형식: ^ 구분자로 분리된 필드들
    """

    RSYM: str
    """실시간종목코드 (예: DNASNVDA)"""

    SYMB: str
    """종목코드 (예: NVDA)"""

    ZDIV: str
    """소수점자리수"""

    TYMD: str
    """현지영업일자"""

    XYMD: str
    """현지일자"""

    XHMS: str
    """현지시간"""

    KYMD: str
    """한국일자"""

    KHMS: str
    """한국시간"""

    OPEN: str
    """시가"""

    HIGH: str
    """고가"""

    LOW: str
    """저가"""

    LAST: str
    """현재가"""

    SIGN: str
    """대비구분"""

    DIFF: str
    """전일대비"""

    RATE: str
    """등락율"""

    PBID: str
    """매수호가"""

    PASK: str
    """매도호가"""

    VBID: str
    """매수잔량"""

    VASK: str
    """매도잔량"""

    EVOL: str
    """체결량"""

    TVOL: str
    """거래량"""

    TAMT: str
    """거래대금"""

    @property
    def exchange_code(self) -> str:
        """거래소 코드 추출 (RSYM에서 D + 3자리 거래소코드 + 심볼)."""
        # 예: DNASNVDA → NAS
        if len(self.RSYM) > 4:
            return self.RSYM[1:4]
        return "NAS"
