"""Adapters layer - 외부 시스템 어댑터."""

from quote_pipeline.adapters.base_adapter import BaseAdapter
from quote_pipeline.adapters.upbit.upbit_adapter import UpbitAdapter

__all__ = ["BaseAdapter", "UpbitAdapter"]
