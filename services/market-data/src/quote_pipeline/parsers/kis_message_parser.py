"""KIS message parser - KIS WebSocket 메시지 파서."""

import json
import logging
from typing import List, Union

from quote_pipeline.domain.kis_domestic_quote_dto import KisDomesticQuoteDTO
from quote_pipeline.domain.kis_overseas_quote_dto import KisOverseasQuoteDTO
from quote_pipeline.domain.kis_subscription_response_dto import KisSubscriptionResponseDTO
from quote_pipeline.parsers.message_parser import MessageParser

logger = logging.getLogger(__name__)


class KisMessageParser(MessageParser):
    """
    KIS WebSocket raw 메시지 파서.

    KIS는 두 가지 메시지 형식을 사용합니다:
    1. Pipe-delimited 형식: "0|HDFSCNT0|001|DNASNVDA^NVDA^..."
    2. JSON 형식: {"header": {...}, "body": {...}}
    """

    def parse(
        self, raw_message: str
    ) -> List[Union[KisOverseasQuoteDTO, KisDomesticQuoteDTO, KisSubscriptionResponseDTO]]:
        """
        raw 메시지를 파싱하여 DTO 리스트로 변환합니다.

        Args:
            raw_message: WebSocket에서 수신한 원본 메시지

        Returns:
            파싱된 DTO 객체들의 리스트
        """
        tr_id = self._detect_tr_id(raw_message)

        if tr_id == "HDFSCNT0":
            # 해외주식 실시간 체결가 (pipe-delimited)
            dto = self._parse_overseas_realtime(raw_message)
            return [dto] if dto else []

        elif tr_id == "H0UNCNT0":
            # 국내주식 실시간 체결가 (pipe-delimited)
            dto = self._parse_domestic_realtime(raw_message)
            return [dto] if dto else []

        else:
            # JSON 형식 (구독 응답 등)
            dto = self._parse_json_response(raw_message)
            return [dto] if dto else []

    def _detect_tr_id(self, msg: str) -> str:
        """
        메시지에서 TR_ID를 추출합니다.

        Args:
            msg: 원본 메시지

        Returns:
            TR_ID (HDFSCNT0, H0UNCNT0 등) 또는 "UNKNOWN"
        """
        # 파이프 형식: "0|HDFSCNT0|001|..." 또는 "0|H0UNCNT0|001|..."
        if msg.startswith("0|") or msg.startswith("1|"):
            parts = msg.split("|")
            if len(parts) >= 2:
                return parts[1]

        # JSON 형식
        try:
            data = json.loads(msg)
            if isinstance(data, dict):
                header = data.get("header", {})
                return header.get("tr_id", "UNKNOWN")
        except json.JSONDecodeError:
            pass

        return "UNKNOWN"

    def _parse_overseas_realtime(self, raw_msg: str) -> KisOverseasQuoteDTO | None:
        """
        해외주식 실시간 체결가 메시지를 파싱합니다.

        데이터 형식: "0|HDFSCNT0|001|DNASNVDA^NVDA^..."
        필드는 ^ 구분자로 분리됩니다.

        Args:
            raw_msg: 원본 메시지

        Returns:
            KisOverseasQuoteDTO 또는 None
        """
        try:
            # "|" 로 분리: [암호화여부, TR_ID, 건수, 데이터]
            parts = raw_msg.split("|")
            if len(parts) < 4:
                return None

            data_part = parts[3]
            fields = data_part.split("^")

            if len(fields) < 21:
                logger.debug("[kis][overseas] Not enough fields: %d", len(fields))
                return None

            return KisOverseasQuoteDTO(
                RSYM=fields[0],
                SYMB=fields[1],
                ZDIV=fields[2],
                TYMD=fields[3],
                XYMD=fields[4],
                XHMS=fields[5],
                KYMD=fields[6],
                KHMS=fields[7],
                OPEN=fields[8],
                HIGH=fields[9],
                LOW=fields[10],
                LAST=fields[11],
                SIGN=fields[12],
                DIFF=fields[13],
                RATE=fields[14],
                PBID=fields[15],
                PASK=fields[16],
                VBID=fields[17],
                VASK=fields[18],
                EVOL=fields[19],
                TVOL=fields[20],
                TAMT=fields[21] if len(fields) > 21 else "",
            )
        except Exception as e:
            logger.warning("[kis][overseas] Parse error: %s", e)
            return None

    def _parse_domestic_realtime(self, raw_msg: str) -> KisDomesticQuoteDTO | None:
        """
        국내주식 실시간 체결가(통합) 메시지를 파싱합니다.

        데이터 형식: "0|H0UNCNT0|001|005930^191053^108000^..."
        필드는 ^ 구분자로 분리됩니다.

        Args:
            raw_msg: 원본 메시지

        Returns:
            KisDomesticQuoteDTO 또는 None
        """
        try:
            # "|" 로 분리: [암호화여부, TR_ID, 건수, 데이터]
            parts = raw_msg.split("|")
            if len(parts) < 4:
                logger.warning("[KisParser] Domestic message has less than 4 parts: %d", len(parts))
                return None

            data_part = parts[3]
            fields = data_part.split("^")

            # H0UNCNT0 필드는 최소 40개 이상
            if len(fields) < 40:
                logger.warning("[KisParser] Domestic message has insufficient fields: %d (expected >= 40)", len(fields))
                return None

            logger.debug(
                "[KisParser] Parsing domestic quote: symbol=%s, price=%s, volume=%s, fields=%d",
                fields[0], fields[2], fields[13], len(fields)
            )

            return KisDomesticQuoteDTO(
                MKSC_SHRN_ISCD=fields[0],       # 종목코드
                STCK_CNTG_HOUR=fields[1],       # 체결시간
                STCK_PRPR=fields[2],            # 현재가
                PRDY_VRSS_SIGN=fields[3],       # 전일대비부호
                PRDY_VRSS=fields[4],            # 전일대비
                PRDY_CTRT=fields[5],            # 전일대비율
                WGHN_AVRG_STCK_PRC=fields[6],   # 가중평균가
                STCK_OPRC=fields[7],            # 시가
                STCK_HGPR=fields[8],            # 고가
                STCK_LWPR=fields[9],            # 저가
                ASKP1=fields[10],               # 매도호가1
                BIDP1=fields[11],               # 매수호가1
                CNTG_VOL=fields[12],            # 체결거래량
                ACML_VOL=fields[13],            # 누적거래량
                ACML_TR_PBMN=fields[14],        # 누적거래대금
                SELN_CNTG_CSNU=fields[15],      # 매도체결건수
                SHNU_CNTG_CSNU=fields[16],      # 매수체결건수
                NTBY_CNTG_CSNU=fields[17],      # 순매수체결건수
                CTTR=fields[18],                # 체결강도
                SELN_CNTG_SMTN=fields[19],      # 총매도수량
                SHNU_CNTG_SMTN=fields[20],      # 총매수수량
                CCLD_DVSN=fields[21],           # 체결구분
                SHNU_RATE=fields[22],           # 매수비율
                PRDY_VOL_VRSS_ACML_VOL_RATE=fields[23],  # 전일거래량대비
                OPRC_HOUR=fields[24],           # 시가시간
                OPRC_VRSS_PRPR_SIGN=fields[25], # 시가대비구분
                OPRC_VRSS_PRPR=fields[26],      # 시가대비
                HGPR_HOUR=fields[27],           # 고가시간
                HGPR_VRSS_PRPR_SIGN=fields[28], # 고가대비구분
                HGPR_VRSS_PRPR=fields[29],      # 고가대비
                LWPR_HOUR=fields[30],           # 저가시간
                LWPR_VRSS_PRPR_SIGN=fields[31], # 저가대비구분
                LWPR_VRSS_PRPR=fields[32],      # 저가대비
                BSOP_DATE=fields[33],           # 영업일자
                NEW_MKOP_CLS_CODE=fields[34],   # 장운영구분
                TRHT_YN=fields[35],             # 거래정지여부
                ASKP_RSQN1=fields[36],          # 매도호가잔량1
                BIDP_RSQN1=fields[37],          # 매수호가잔량1
                TOTAL_ASKP_RSQN=fields[38],     # 총매도호가잔량
                TOTAL_BIDP_RSQN=fields[39],     # 총매수호가잔량
                VOL_TNRT=fields[40] if len(fields) > 40 else "",
                PRDY_SMNS_HOUR_ACML_VOL=fields[41] if len(fields) > 41 else "",
                PRDY_SMNS_HOUR_ACML_VOL_RATE=fields[42] if len(fields) > 42 else "",
                HOUR_CLS_CODE=fields[43] if len(fields) > 43 else "",
                MRKT_TRTM_CLS_CODE=fields[44] if len(fields) > 44 else "",
                VI_STND_PRC=fields[45] if len(fields) > 45 else "",
            )
        except Exception as e:
            logger.warning("[KisParser] Domestic parse error: %s (raw=%s)", e, raw_msg[:100])
            return None

    def _parse_json_response(self, raw_msg: str) -> KisSubscriptionResponseDTO | None:
        """
        JSON 형식의 응답 메시지를 파싱합니다.

        주로 구독 성공/실패 응답에 사용됩니다.

        Args:
            raw_msg: 원본 메시지 (JSON 형식)

        Returns:
            KisSubscriptionResponseDTO 또는 None
        """
        try:
            data = json.loads(raw_msg)
            if not isinstance(data, dict):
                return None

            header = data.get("header", {})
            body = data.get("body", {})

            return KisSubscriptionResponseDTO(
                tr_id=header.get("tr_id", "UNKNOWN"),
                tr_key=header.get("tr_key") or body.get("tr_key"),
                rt_cd=header.get("rt_cd"),
                msg_cd=body.get("msg_cd"),
                msg=body.get("msg"),
                output=body.get("output") if isinstance(body.get("output"), dict) else None,
            )
        except json.JSONDecodeError:
            logger.debug("[kis] Failed to parse JSON response")
            return None
        except Exception as e:
            logger.debug("[kis] JSON parse error: %s", e)
            return None
