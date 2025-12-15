"""Message parser - 메시지 파서 추상 클래스."""

from abc import ABC, abstractmethod
from typing import Any, List


class MessageParser(ABC):
    """
    메시지 파서 추상 클래스.

    raw string → DTO(s) 변환을 담당합니다.
    비즈니스 로직 없이 순수 파싱만 수행합니다.
    """

    @abstractmethod
    def parse(self, raw_message: str) -> List[Any]:
        """
        raw 메시지를 파싱하여 DTO 리스트로 변환합니다.

        Args:
            raw_message: 원본 메시지 (WebSocket에서 수신한 raw string)

        Returns:
            파싱된 DTO 객체들의 리스트.
            파싱 실패 시 빈 리스트 반환.
        """
        pass
