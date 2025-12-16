"""KIS subscription response DTO - KIS WebSocket 구독 응답 데이터 전송 객체."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class KisSubscriptionResponseDTO:
    """
    KIS WebSocket 구독 응답 (JSON 형식).

    구독 성공/실패 등의 응답 메시지를 파싱합니다.
    """

    tr_id: str
    """TR_ID (HDFSCNT0, H0UNCNT0 등)"""

    tr_key: Optional[str] = None
    """TR_KEY (심볼 또는 RSYM)"""

    rt_cd: Optional[str] = None
    """응답 코드 (0: 성공)"""

    msg_cd: Optional[str] = None
    """메시지 코드"""

    msg: Optional[str] = None
    """메시지 내용"""

    output: Optional[dict] = None
    """body.output 필드 (있는 경우)"""
