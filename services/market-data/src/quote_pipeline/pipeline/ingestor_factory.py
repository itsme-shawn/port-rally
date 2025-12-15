"""Ingestor factory - QuoteIngestor 팩토리."""

import logging
from typing import Iterable

from quote_pipeline.adapters.kis.kis_adapter import KisAdapter
from quote_pipeline.adapters.kis.kis_config import KisConfig
from quote_pipeline.adapters.kis.kis_auth_client import KisWsAuthClient
from quote_pipeline.adapters.upbit.upbit_adapter import UpbitAdapter
from quote_pipeline.config import Provider, Settings
from quote_pipeline.mappers.kis_quote_mapper import KisQuoteMapper
from quote_pipeline.mappers.upbit_quote_mapper import UpbitQuoteMapper
from quote_pipeline.parsers.kis_message_parser import KisMessageParser
from quote_pipeline.parsers.upbit_message_parser import UpbitMessageParser
from quote_pipeline.pipeline.quote_ingestor import QuoteIngestor
from quote_pipeline.publishers.base_publisher import BasePublisher
from quote_pipeline.services.subscription_service import SubscriptionService
from quote_pipeline.services.symbol_service import SymbolService

logger = logging.getLogger(__name__)


class IngestorFactory:
    """
    QuoteIngestor 팩토리.

    Provider별로 필요한 의존성(Adapter, Parser, Mapper, Services)을
    조립하여 QuoteIngestor를 생성합니다.

    기존 pipeline.py의 build_ingestor() 로직을 개선했습니다.
    """

    @staticmethod
    def create_kis_ingestor(
        symbols: Iterable[str],
        publisher: BasePublisher,
        appkey: str,
        appsecret: str,
        exchange: str = "NAS",
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 20.0,
        db_pool=None,
    ) -> QuoteIngestor:
        """
        KIS QuoteIngestor를 생성합니다.

        Args:
            symbols: 구독할 심볼 리스트
            publisher: 출력 publisher
            appkey: KIS API Key
            appsecret: KIS API Secret
            exchange: 기본 거래소 코드 (NAS, NYS 등)
            reconnect_base_delay: 재연결 기본 지연 (초)
            reconnect_max_delay: 재연결 최대 지연 (초)
            db_pool: 데이터베이스 연결 풀 (Optional)

        Returns:
            QuoteIngestor 인스턴스
        """
        logger.info("[IngestorFactory] Creating KIS ingestor for %d symbols", len(list(symbols)))

        # 1. Services 생성
        symbol_service = SymbolService(db_pool=db_pool)
        subscription_service = SubscriptionService()

        # 2. KIS 클라이언트 설정
        config = KisConfig(app_key=appkey, app_secret=appsecret)
        auth_client = KisWsAuthClient(config)

        # 3. Adapter 생성
        adapter = KisAdapter(
            config=config,
            auth_client=auth_client,
            subscription_service=subscription_service,
            exchange=exchange,
        )

        # 4. Parser 생성
        parser = KisMessageParser()

        # 5. Mapper 생성
        mapper = KisQuoteMapper(symbol_service=symbol_service)

        # 6. QuoteIngestor 조립
        ingestor = QuoteIngestor(
            adapter=adapter,
            parser=parser,
            mapper=mapper,
            publisher=publisher,
            symbols=symbols,
            reconnect_base_delay=reconnect_base_delay,
            reconnect_max_delay=reconnect_max_delay,
        )

        logger.info("[IngestorFactory] KIS ingestor created successfully")
        return ingestor

    @staticmethod
    def create_upbit_ingestor(
        symbols: Iterable[str],
        publisher: BasePublisher,
        url: str,
        channel: str = "ticker",
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 20.0,
    ) -> QuoteIngestor:
        """Upbit QuoteIngestor 생성."""
        logger.info("[IngestorFactory] Creating Upbit ingestor for %d symbols", len(list(symbols)))

        adapter = UpbitAdapter(url=url, channel=channel)
        parser = UpbitMessageParser()
        mapper = UpbitQuoteMapper()

        return QuoteIngestor(
            adapter=adapter,
            parser=parser,
            mapper=mapper,
            publisher=publisher,
            symbols=symbols,
            reconnect_base_delay=reconnect_base_delay,
            reconnect_max_delay=reconnect_max_delay,
        )

    @staticmethod
    def create_ingestor(
        settings: Settings,
        provider: Provider,
        publisher: BasePublisher,
        db_pool=None,
    ) -> QuoteIngestor:
        """
        Settings와 Provider에 따라 QuoteIngestor를 생성합니다.

        기존 build_ingestor()를 대체하는 메서드입니다.

        Args:
            settings: 파이프라인 설정
            provider: Provider 타입
            publisher: 출력 publisher
            db_pool: 데이터베이스 연결 풀 (Optional)

        Returns:
            QuoteIngestor 인스턴스

        Raises:
            ValueError: 지원하지 않는 provider인 경우
        """
        if provider == Provider.kis:
            return IngestorFactory.create_kis_ingestor(
                symbols=settings.symbols,
                publisher=publisher,
                appkey=settings.kis.appkey,
                appsecret=settings.kis.secretkey,
                exchange=settings.kis.exchange if hasattr(settings.kis, "exchange") else "NAS",
                reconnect_base_delay=settings.common.reconnect_base_delay,
                reconnect_max_delay=settings.common.reconnect_max_delay,
                db_pool=db_pool,
            )

        if provider == Provider.upbit:
            return IngestorFactory.create_upbit_ingestor(
                symbols=settings.symbols,
                publisher=publisher,
                url=settings.upbit.url,
                channel=settings.upbit.channel,
                reconnect_base_delay=settings.common.reconnect_base_delay,
                reconnect_max_delay=settings.common.reconnect_max_delay,
            )
        # elif provider == Provider.binance:
        #     return IngestorFactory.create_binance_ingestor(...)

        raise ValueError(f"Unsupported provider: {provider}. Only KIS is refactored for now.")
