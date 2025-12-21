"""Ingestor factory - BaseIngestor 팩토리 및 빌드 유틸리티."""

import logging
from typing import Iterable, Optional

from quote_pipeline.clients.kis.kis_client import KisClient
from quote_pipeline.clients.kis.kis_config import KisConfig
from quote_pipeline.clients.kis.kis_auth_client import KisWsAuthClient
from quote_pipeline.clients.upbit.upbit_client import UpbitClient
from quote_pipeline.config import Provider, Settings
from quote_pipeline.mappers.kis_quote_mapper import KisQuoteMapper
from quote_pipeline.mappers.upbit_quote_mapper import UpbitQuoteMapper
from quote_pipeline.parsers.kis_message_parser import KisMessageParser
from quote_pipeline.parsers.upbit_message_parser import UpbitMessageParser
from quote_pipeline.ingestors.base_ingestor import BaseIngestor
from quote_pipeline.publishers.base_publisher import BasePublisher
from quote_pipeline.publishers.redis_publisher import RedisPublisher
from quote_pipeline.publishers.stdout_publisher import StdoutPublisher
from quote_pipeline.services.subscription_service import SubscriptionService
from quote_pipeline.services.symbol_service import SymbolService
from quote_pipeline.stores import QuoteStore

logger = logging.getLogger(__name__)


class IngestorFactory:
    """
    BaseIngestor 팩토리.

    Provider별로 필요한 의존성(Client, Parser, Mapper, Services)을
    조립하여 BaseIngestor를 생성합니다.

    또한 Publisher, QuoteStore 생성 유틸리티 메서드도 포함합니다.
    """

    # =========================================================================
    # Ingestor 생성 메서드
    # =========================================================================

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
    ) -> BaseIngestor:
        """
        KIS BaseIngestor를 생성합니다.

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
            BaseIngestor 인스턴스
        """
        logger.info("[IngestorFactory] Creating KIS ingestor for %d symbols", len(list(symbols)))

        # 1. Services 생성
        symbol_service = SymbolService(db_pool=db_pool)
        subscription_service = SubscriptionService()

        # 2. KIS 클라이언트 설정
        config = KisConfig(app_key=appkey, app_secret=appsecret)
        auth_client = KisWsAuthClient(config)

        # 3. Client 생성
        client = KisClient(
            config=config,
            auth_client=auth_client,
            subscription_service=subscription_service,
            exchange=exchange,
        )

        # 4. Parser 생성
        parser = KisMessageParser()

        # 5. Mapper 생성
        mapper = KisQuoteMapper(symbol_service=symbol_service)

        # 6. BaseIngestor 조립
        ingestor = BaseIngestor(
            client=client,
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
    ) -> BaseIngestor:
        """Upbit BaseIngestor 생성."""
        logger.info("[IngestorFactory] Creating Upbit ingestor for %d symbols", len(list(symbols)))

        client = UpbitClient(url=url, channel=channel)
        parser = UpbitMessageParser()
        mapper = UpbitQuoteMapper()

        return BaseIngestor(
            client=client,
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
    ) -> BaseIngestor:
        """
        Settings와 Provider에 따라 BaseIngestor를 생성합니다.

        Args:
            settings: 파이프라인 설정
            provider: Provider 타입
            publisher: 출력 publisher
            db_pool: 데이터베이스 연결 풀 (Optional)

        Returns:
            BaseIngestor 인스턴스

        Raises:
            ValueError: 지원하지 않는 provider인 경우
        """
        if provider == Provider.kis:
            appkey = settings.kis.appkey
            appsecret = settings.kis.secretkey

            if appkey is None or appsecret is None:
                raise ValueError("KIS appkey/appsecret must be provided in settings or environment variables")

            return IngestorFactory.create_kis_ingestor(
                symbols=settings.symbols,
                publisher=publisher,
                appkey=appkey,
                appsecret=appsecret,
                exchange=settings.kis.exchange if hasattr(settings.kis, "exchange") else "NAS", # type: ignore
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

        raise ValueError(f"Unsupported provider: {provider}")

    # =========================================================================
    # Publisher/Store 빌드 메서드 (기존 build_pipeline.py 통합)
    # =========================================================================

    @staticmethod
    def build_publisher(settings: Settings) -> BasePublisher:
        """
        Settings에 따라 적절한 Publisher를 생성합니다.

        Args:
            settings: 파이프라인 설정

        Returns:
            BasePublisher 인스턴스 (RedisPublisher 또는 StdoutPublisher)
        """
        # env 우선 적용 (run 시 -e REDIS_URL=stdout 등)
        url = settings.redis.url or ""
        sentinel = ("", "null", "none", "stdout")
        if url.strip().lower() in sentinel:
            logger.info("Using StdoutPublisher")
            return StdoutPublisher()
        logger.info("Using RedisPublisher url=%s channel=%s", url, settings.redis.channel)
        return RedisPublisher(url=url, channel=settings.redis.channel)

    @staticmethod
    def build_store(settings: Settings) -> Optional[QuoteStore]:
        """
        Redis URL이 설정된 경우 QuoteStore 인스턴스를 생성한다.

        Args:
            settings: 파이프라인 설정

        Returns:
            QuoteStore 인스턴스 또는 None (Redis URL 미설정 시)
        """
        url = settings.redis.url or ""
        sentinel = ("", "null", "none", "stdout")
        if url.strip().lower() in sentinel:
            logger.info("QuoteStore disabled (no Redis URL)")
            return None

        store = QuoteStore(
            redis_url=url,
            channel=settings.redis.channel,
            key_prefix="quote",
        )
        logger.info("Built QuoteStore: channel=%s", settings.redis.channel)
        return store
