from abc import ABC, abstractmethod
from typing import Any, Dict


class Sink(ABC):
    @abstractmethod
    async def publish(self, payload: Dict[str, Any]) -> None:
        """Persist or forward parsed payloads."""
        raise NotImplementedError
