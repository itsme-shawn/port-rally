"""Base publisher - 출력 포트 추상화."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePublisher(ABC):
    """
    출력 포트 추상화 클래스.

    도메인 이벤트를 외부 시스템으로 발행합니다.
    """

    @abstractmethod
    async def publish(self, payload: Dict[str, Any]) -> None:
        """
        페이로드를 발행합니다.

        Args:
            payload: 발행할 데이터 (dict)
        """
        raise NotImplementedError
