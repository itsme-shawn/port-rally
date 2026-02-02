# This is a stub file for type hinting.
# It allows static analyzers (like in an IDE) to understand the
# dynamically created attributes of the 'meta' object.
from typing import Any, Dict, Optional

class _RedisKeyBuilder:
    """Represents a Redis key builder with its methods."""

    def __call__(self, **kwargs: Any) -> "_RedisKeyBuilder":
        """Allows calling the key like a function, e.g., meta.quote(symbol='BTC')."""
        ...

    def build(self) -> str:
        """Builds the final Redis key string."""
        ...

    def get_pattern(self, **kwargs: Any) -> str:
        """Gets the key pattern, optionally with wildcards."""
        ...

    def parse(self, key: str) -> Optional[Dict[str, str]]:
        """Parses a key string into its components."""
        ...

    def get_prefix(self) -> str:
        """Gets the key's prefix."""
        ...

    def get_ttl_seconds(self) -> Optional[int]:
        """Gets the key's TTL in seconds."""
        ...

class _ChannelBuilder:
    """Represents a Pub/Sub channel."""
    pattern: str

class _Meta:
    """Defines the attributes of the 'meta' object."""
    refresh_token: _RedisKeyBuilder
    user_refresh: _RedisKeyBuilder
    quote: _RedisKeyBuilder
    active_symbols: _RedisKeyBuilder
    symbol_metadata: _RedisKeyBuilder
    symbol_map: _RedisKeyBuilder
    symbol_detail: _RedisKeyBuilder
    quotes: _ChannelBuilder

# The global 'meta' object that is imported from this package.
meta: _Meta
