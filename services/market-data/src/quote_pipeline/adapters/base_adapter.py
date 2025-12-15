"""Base adapter - 외부 데이터 소스 어댑터 추상화."""

from abc import ABC, abstractmethod
from typing import Iterable


class BaseAdapter(ABC):
    """
    외부 데이터 소스 어댑터 추상 클래스.

    WebSocket, REST API 등 외부 시스템과의 통신을 담당합니다.
    Hexagonal Architecture의 입력 포트 역할을 합니다.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        외부 시스템과 연결을 수립합니다.

        WebSocket 연결, REST API 인증 등을 수행합니다.
        """
        pass

    @abstractmethod
    async def subscribe(self, symbols: Iterable[str]) -> None:
        """
        심볼 구독을 등록합니다.

        Args:
            symbols: 구독할 심볼 리스트
        """
        pass

    @abstractmethod
    async def receive(self) -> str:
        """
        메시지를 수신합니다.

        Returns:
            수신된 raw 메시지 (string)
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        연결을 종료합니다.

        리소스 정리 및 연결 해제를 수행합니다.
        """
        pass

    async def apply_symbols(self, symbols: Iterable[str]) -> None:
        """
        동적으로 심볼 구독을 변경합니다.

        WebSocket 재연결 없이 구독 목록을 변경합니다.
        기본 구현은 subscribe()를 호출하며, 필요시 오버라이드 가능합니다.

        Args:
            symbols: 새로운 구독 심볼 리스트
        """
        await self.subscribe(symbols)
