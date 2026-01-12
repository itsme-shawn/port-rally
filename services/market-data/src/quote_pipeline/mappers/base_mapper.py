"""Base mapper - DTO → Domain 변환 추상화."""

from abc import ABC, abstractmethod
from typing import Any

from quote_pipeline.domain.uni_quote_dto import UniQuoteDto


class BaseMapper(ABC):
    """
    DTO → Domain Event 변환 추상 클래스.

    Provider별 DTO를 통합 도메인 DTO(UniQuoteDto)로 변환합니다.
    Spring의 ModelMapper, MapStruct와 유사한 역할을 합니다.
    """

    @abstractmethod
    async def to_uni_quote(self, dto: Any) -> UniQuoteDto | None:
        """
        Provider별 DTO를 UniQuoteDto로 변환합니다.

        Args:
            dto: Provider별 DTO (KisOverseasQuoteDTO, UpbitQuoteDTO 등)

        Returns:
            UniQuoteDto 또는 None (변환 실패 시)
        """
        pass
