import json
from typing import Any, Dict

from .base import Sink


class StdoutSink(Sink):
    def __init__(self, indent: bool = False) -> None:
        self.indent = indent

    async def publish(self, payload: Dict[str, Any]) -> None:
        msg = json.dumps(payload, ensure_ascii=False, indent=2 if self.indent else None)
        print(msg, flush=True)
