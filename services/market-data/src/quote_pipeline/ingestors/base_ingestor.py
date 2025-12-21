"""Base ingestor - 시세 수집 파이프라인 orchestrator."""

import asyncio
import logging
from typing import Iterable

from websockets.exceptions import ConnectionClosed

from quote_pipeline.clients.base_client import BaseClient
from quote_pipeline.mappers.base_mapper import BaseMapper
from quote_pipeline.parsers.message_parser import MessageParser
from quote_pipeline.publishers.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class BaseIngestor:
    """
    시세 수집 파이프라인 정의 class.

    모든 레이어(Client, Parser, Mapper, Publisher)를 조합하여
    데이터 파이프라인을 만든다

    각 provider별 의존성 주입은 ingestor_factory 에서 수행한다

    데이터 파이프라인:
    1. Client: WebSocket에서 raw 메시지 수신
    2. Parser: raw 메시지 → Provider DTO
    3. Mapper: Provider DTO → UniQuoteDto
    4. Publisher: UniQuoteDto를 외부로 발행 (redis, stdout..)
    """

    def __init__(
        self,
        client: BaseClient,
        parser: MessageParser,
        mapper: BaseMapper,
        publisher: BasePublisher,
        symbols: Iterable[str],
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 20.0,
    ):
        """
        BaseIngestor 초기화.

        Args:
            client: 외부 시스템 클라이언트
            parser: 메시지 파서
            mapper: DTO → UniQuoteDto 매퍼
            publisher: 출력 publisher
            symbols: 구독할 심볼 리스트
            reconnect_base_delay: 재연결 기본 지연 시간 (초)
            reconnect_max_delay: 재연결 최대 지연 시간 (초)
        """
        self.client = client
        self.parser = parser
        self.mapper = mapper
        self.publisher = publisher
        self.symbols = set(symbols)
        self.reconnect_base_delay = reconnect_base_delay
        self.reconnect_max_delay = reconnect_max_delay

    async def run_forever(self) -> None:
        """
        파이프라인을 무한 실행합니다.

        재연결 로직을 포함하여 안정적으로 동작합니다.
        """
        delay = self.reconnect_base_delay

        while True:
            try:
                await self._stream_once()
                delay = self.reconnect_base_delay  # 성공 시 delay 초기화
            except ConnectionClosed as exc:
                logger.warning(
                    "[BaseIngestor] WebSocket closed code=%s reason=%s; retrying in %.1fs",
                    getattr(exc, "code", None),
                    getattr(exc, "reason", None),
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)
            except asyncio.CancelledError:
                logger.info("[BaseIngestor] Cancelled, shutting down")
                raise
            except Exception:
                logger.exception("[BaseIngestor] Stream error, retrying in %.1fs", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)

    async def _stream_once(self) -> None:
        """
        한 번의 스트리밍 세션을 실행합니다.

        연결 → 구독 → 메시지 수신 루프 → 연결 종료
        """
        if not self.symbols:
            logger.info("[BaseIngestor] No symbols to subscribe, sleeping")
            await asyncio.sleep(1)
            return

        logger.info("[BaseIngestor] Connecting with %d symbols: %s", len(self.symbols), self.symbols)

        try:
            # 1. 연결
            logger.info("[BaseIngestor] Step 1: Connecting to client...")
            await self.client.connect()
            logger.info("[BaseIngestor] Step 1: Connected successfully")

            # 2. 구독
            logger.info("[BaseIngestor] Step 2: Subscribing to symbols...")
            await self.client.subscribe(self.symbols)
            logger.info("[BaseIngestor] Step 2: Subscribed successfully")

            # 3. 메시지 수신 루프
            logger.info("[BaseIngestor] Step 3: Starting message receive loop...")
            msg_count = 0
            while True:
                await self._handle_message()
                msg_count += 1
                if msg_count % 100 == 0:
                    logger.info("[BaseIngestor] Received %d messages so far", msg_count)

        except ConnectionClosed:
            raise  # 상위에서 재연결 처리
        finally:
            # 4. 연결 종료
            await self.client.close()

    async def _handle_message(self) -> None:
        """
        메시지를 수신하고 처리합니다.

        데이터 흐름: Client → Parser → Mapper → Publisher
        """
        # 1. Client: raw 메시지 수신
        raw_message = await self.client.receive()
        logger.debug("[BaseIngestor] Raw message received: %s", raw_message[:200] if len(raw_message) > 200 else raw_message)

        # 2. Parser: raw → DTO
        dtos = self.parser.parse(raw_message)
        logger.debug("[BaseIngestor] Parsed %d DTOs from message", len(dtos))

        # 3. Mapper + Publisher: DTO → UniQuoteDto → publish
        for dto in dtos:
            uni_quote = self.mapper.to_uni_quote(dto)

            if uni_quote:
                # 4. Publisher: UniQuoteDto를 외부로 발행
                payload = uni_quote.to_dict()
                logger.debug("[BaseIngestor] Publishing: symbol=%s, price=%s", payload.get("data", {}).get("symbol"), payload.get("data", {}).get("price"))
                await self.publisher.publish(payload)
            else:
                logger.debug("[BaseIngestor] Failed to map DTO to UniQuoteDto: %s", type(dto))

    async def apply_symbols(self, symbols: Iterable[str]) -> None:
        """
        동적으로 구독 심볼을 변경합니다.

        WebSocket 재연결 없이 구독 목록을 변경합니다.

        Args:
            symbols: 새로운 구독 심볼 리스트
        """
        self.symbols = set(symbols)
        await self.client.apply_symbols(symbols)
        logger.info("[BaseIngestor] Applied new symbols: %d", len(symbols))
