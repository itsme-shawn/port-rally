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
    KIS WebSocket 메시지 파서.

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

        elif tr_id == "H0STCNT0":
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
            TR_ID (HDFSCNT0, H0STCNT0 등) 또는 "UNKNOWN"
        """
        # 파이프 형식: "0|HDFSCNT0|001|..." 또는 "0|H0STCNT0|001|..."
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
            logger.debug("[kis][overseas] Parse error: %s", e)
            return None

    def _parse_domestic_realtime(self, raw_msg: str) -> KisDomesticQuoteDTO | None:
        """
        국내주식 실시간 체결가 메시지를 파싱합니다.

        TODO: 추후 실제 데이터 형식 확인 후 구현

        Args:
            raw_msg: 원본 메시지

        Returns:
            KisDomesticQuoteDTO 또는 None
        """
        # 국내주식은 JSON 형태로 오는 경우와 pipe 형태로 오는 경우가 있음
        # 추후 실제 데이터 형식 확인 후 구현
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
