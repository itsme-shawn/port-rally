"""Subscription service - 구독 상태 추적 서비스."""

import logging
from typing import Dict, Iterable, Set, Tuple

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    구독 상태 추적 서비스.

    WebSocket 구독 상태를 관리하고, 구독 변경사항을 계산합니다.
    """

    def __init__(self):
        """SubscriptionService 초기화."""
        # key: (tr_id, symbol), value: tr_key
        self._subscribed: Dict[Tuple[str, str], str] = {}

    def mark_subscribed(self, tr_id: str, symbol: str, tr_key: str) -> None:
        """
        구독 성공 시 호출하여 상태를 기록합니다.

        Args:
            tr_id: TR_ID (H0UNCNT0, HDFSCNT0 등)
            symbol: 심볼 (NVDA, 005930 등)
            tr_key: TR_KEY (구독 요청 시 사용한 키)
        """
        key = (tr_id, symbol)
        self._subscribed[key] = tr_key
        logger.debug("[SubscriptionService] Marked subscribed: %s → %s", key, tr_key)

    def mark_unsubscribed(self, tr_id: str, symbol: str) -> None:
        """
        구독 해제 시 호출하여 상태를 제거합니다.

        Args:
            tr_id: TR_ID
            symbol: 심볼
        """
        key = (tr_id, symbol)
        if key in self._subscribed:
            del self._subscribed[key]
            logger.debug("[SubscriptionService] Marked unsubscribed: %s", key)

    def is_subscribed(self, tr_id: str, symbol: str) -> bool:
        """
        특정 TR_ID + 심볼이 구독 중인지 확인합니다.

        Args:
            tr_id: TR_ID
            symbol: 심볼

        Returns:
            구독 중이면 True
        """
        return (tr_id, symbol) in self._subscribed

    def get_tr_key(self, tr_id: str, symbol: str) -> str | None:
        """
        구독 중인 TR_KEY를 조회합니다.

        Args:
            tr_id: TR_ID
            symbol: 심볼

        Returns:
            TR_KEY 또는 None
        """
        return self._subscribed.get((tr_id, symbol))

    def calculate_changes(
        self,
        desired_subscriptions: Dict[Tuple[str, str], str],
    ) -> Tuple[Dict[Tuple[str, str], str], Dict[Tuple[str, str], str]]:
        """
        현재 구독 상태와 원하는 구독 상태를 비교하여 변경사항을 계산합니다.

        기존 `KisIngestor.apply_symbols()` 로직을 추출.

        Args:
            desired_subscriptions: 원하는 구독 목록 {(tr_id, symbol): tr_key}

        Returns:
            (to_add, to_remove) 튜플
            - to_add: 추가할 구독 {(tr_id, symbol): tr_key}
            - to_remove: 제거할 구독 {(tr_id, symbol): tr_key}
        """
        current_keys = set(self._subscribed.keys())
        desired_keys = set(desired_subscriptions.keys())

        to_add_keys = desired_keys - current_keys
        to_remove_keys = current_keys - desired_keys

        to_add = {key: desired_subscriptions[key] for key in to_add_keys}
        to_remove = {key: self._subscribed[key] for key in to_remove_keys}

        if to_add or to_remove:
            logger.info(
                "[SubscriptionService] Changes: add=%d remove=%d", len(to_add), len(to_remove)
            )

        return to_add, to_remove

    def clear(self) -> None:
        """모든 구독 상태를 초기화합니다."""
        self._subscribed.clear()
        logger.info("[SubscriptionService] All subscriptions cleared")

    def get_subscribed_count(self) -> int:
        """현재 구독 중인 항목 수를 반환합니다."""
        return len(self._subscribed)

    def get_all_subscriptions(self) -> Dict[Tuple[str, str], str]:
        """
        현재 구독 중인 모든 항목을 반환합니다.

        Returns:
            {(tr_id, symbol): tr_key} 딕셔너리
        """
        return self._subscribed.copy()
