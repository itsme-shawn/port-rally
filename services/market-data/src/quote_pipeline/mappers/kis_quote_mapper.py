"""KIS quote mapper - KIS DTO → UniQuoteDto 변환."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from quote_pipeline.domain.kis_domestic_quote_dto import KisDomesticQuoteDTO
from quote_pipeline.domain.kis_overseas_quote_dto import KisOverseasQuoteDTO
from quote_pipeline.domain.kis_subscription_response_dto import KisSubscriptionResponseDTO
from quote_pipeline.domain.uni_quote_dto import UniQuoteDto
from quote_pipeline.mappers.base_mapper import BaseMapper
from quote_pipeline.services.symbol_service import SymbolService

logger = logging.getLogger(__name__)


class KisQuoteMapper(BaseMapper):
    """
    KIS DTO → UniQuoteDto 변환 매퍼.

    KIS provider의 DTO들을 통합 도메인 DTO로 정규화합니다.
    """

    def __init__(self, symbol_service: SymbolService):
        """
        KisQuoteMapper 초기화.

        Args:
            symbol_service: 심볼 정보 조회 서비스
        """
        self.symbol_service = symbol_service

    def to_uni_quote(
        self, dto: KisOverseasQuoteDTO | KisDomesticQuoteDTO | KisSubscriptionResponseDTO
    ) -> UniQuoteDto | None:
        """
        KIS DTO를 UniQuoteDto로 변환합니다.

        Args:
            dto: KIS DTO (Overseas, Domestic, SubscriptionResponse)

        Returns:
            UniQuoteDto 또는 None
        """
        if isinstance(dto, KisOverseasQuoteDTO):
            return self._map_overseas_quote(dto)
        elif isinstance(dto, KisDomesticQuoteDTO):
            return self._map_domestic_quote(dto)
        elif isinstance(dto, KisSubscriptionResponseDTO):
            return self._map_subscription_response(dto)
        else:
            logger.warning("[KisQuoteMapper] Unknown DTO type: %s", type(dto))
            return None

    def _map_overseas_quote(self, dto: KisOverseasQuoteDTO) -> UniQuoteDto | None:
        """
        해외주식 DTO를 UniQuoteDto로 변환합니다.

        Args:
            dto: KisOverseasQuoteDTO

        Returns:
            UniQuoteDto 또는 None
        """
        try:
            # 타임스탬프 파싱 (KYMD + KHMS → datetime)
            timestamp = self._parse_timestamp(dto.KYMD, dto.KHMS)

            logger.debug(
                "[KisQuoteMapper] Mapping overseas quote: symbol=%s, price=%s, volume=%s",
                dto.SYMB, dto.LAST, dto.TVOL
            )

            return UniQuoteDto(
                symbol=dto.SYMB,
                provider="kis",
                price=self._parse_decimal(dto.LAST),
                timestamp=timestamp,
                national="US",  # 기본값 (추후 거래소별 분기 가능)
                market=dto.exchange_code,
                volume=self._parse_decimal(dto.TVOL),
                open=self._parse_decimal(dto.OPEN),
                high=self._parse_decimal(dto.HIGH),
                low=self._parse_decimal(dto.LOW),
                change=self._parse_decimal(dto.DIFF),
                change_rate=self._parse_decimal(dto.RATE),
                metadata={"sign": dto.SIGN, "rsym": dto.RSYM},
            )
        except Exception as e:
            logger.warning("[KisQuoteMapper] Failed to map overseas quote: %s", e)
            return None

    def _map_domestic_quote(self, dto: KisDomesticQuoteDTO) -> UniQuoteDto | None:
        """
        국내주식 DTO를 UniQuoteDto로 변환합니다.

        Args:
            dto: KisDomesticQuoteDTO

        Returns:
            UniQuoteDto 또는 None
        """
        try:
            # 타임스탬프 파싱 (BSOP_DATE + STCK_CNTG_HOUR → datetime)
            timestamp = self._parse_timestamp(dto.BSOP_DATE, dto.STCK_CNTG_HOUR)

            logger.debug(
                "[KisQuoteMapper] Mapping domestic quote: symbol=%s, price=%s, volume=%s",
                dto.symbol, dto.STCK_PRPR, dto.ACML_VOL
            )

            return UniQuoteDto(
                symbol=dto.symbol,
                provider="kis",
                price=self._parse_decimal(dto.STCK_PRPR),
                timestamp=timestamp,
                national="KR",
                market=dto.market,  # KOSPI/KOSDAQ
                volume=self._parse_decimal(dto.ACML_VOL),
                open=self._parse_decimal(dto.STCK_OPRC),
                high=self._parse_decimal(dto.STCK_HGPR),
                low=self._parse_decimal(dto.STCK_LWPR),
                change=self._parse_decimal(dto.PRDY_VRSS),
                change_rate=self._parse_decimal(dto.PRDY_CTRT),
                metadata={
                    "sign": dto.PRDY_VRSS_SIGN,
                    "trade_volume": dto.CNTG_VOL,
                    "strength": dto.CTTR,
                },
            )
        except Exception as e:
            logger.warning("[KisQuoteMapper] Failed to map domestic quote: %s", e)
            return None

    def _map_subscription_response(self, dto: KisSubscriptionResponseDTO) -> UniQuoteDto | None:
        """
        구독 응답 DTO를 UniQuoteDto로 변환합니다.

        구독 응답에 price 정보가 있는 경우에만 변환합니다.

        Args:
            dto: KisSubscriptionResponseDTO

        Returns:
            UniQuoteDto 또는 None
        """
        try:
            # output에 가격 정보가 있는지 확인
            if not dto.output:
                return None

            price = dto.output.get("last") or dto.output.get("tp") or dto.output.get("price")
            volume = dto.output.get("vol") or dto.output.get("tvol")

            if price is None:
                return None

            # TR_KEY에서 심볼 추출
            symbol = dto.tr_key
            if not symbol:
                return None

            # 국내주식인 경우 SymbolService에서 market 조회
            market, national = self.symbol_service.get_market_info(symbol, default_market="KRX")

            return UniQuoteDto(
                symbol=symbol,
                provider="kis",
                price=self._parse_decimal(str(price)),
                timestamp=datetime.now(),  # 구독 응답에는 타임스탬프가 없으므로 현재 시각 사용
                national=national,
                market=market,
                volume=self._parse_decimal(str(volume)) if volume else None,
                metadata={"tr_id": dto.tr_id, "rt_cd": dto.rt_cd},
            )
        except Exception as e:
            logger.warning("[KisQuoteMapper] Failed to map subscription response: %s", e)
            return None

    def _parse_timestamp(self, date_str: str, time_str: str) -> datetime:
        """
        KIS 날짜/시간 문자열을 datetime으로 변환합니다.

        Args:
            date_str: YYYYMMDD 형식 (예: 20231215)
            time_str: HHMMSS 형식 (예: 143000)

        Returns:
            datetime 객체
        """
        try:
            dt_str = f"{date_str}{time_str}"  # 예: 20231215143000
            return datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        except Exception:
            logger.warning("[KisQuoteMapper] Failed to parse timestamp: %s %s", date_str, time_str)
            return datetime.now()

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """
        문자열을 Decimal로 변환합니다.

        Args:
            value: 숫자 문자열

        Returns:
            Decimal 또는 None
        """
        if not value:
            return None
        try:
            return Decimal(value)
        except Exception:
            return None
