"""Redis metadata management system.

Provides type-safe, validated Redis key generation from central schema.

Usage:
    from quote_pipeline.redis_meta import meta

    # Create a quote key with validation
    quote_key = meta.quote(
        national="KR",
        exchange="KOSPI",
        symbol="005930"
    )

    # Build the key string
    redis_key = quote_key.build()  # "quote:KR:KOSPI:005930"

    # Get TTL from schema
    ttl_ms = quote_key.get_ttl()  # 60000
    ttl_sec = quote_key.get_ttl_seconds()  # 60

    # Get Redis type and codec
    key_type = quote_key.get_type()  # "hash"
    codec = quote_key.get_codec()  # "json"
"""

from typing import Any, Dict, Type

from .builder import generate_all_keys
from .models import RedisKeyBase
from .schema import get_schema, reload_schema

__all__ = [
    "meta",
    "RedisMeta",
    "get_schema",
    "reload_schema",
]


class RedisMeta:
    """Central accessor for Redis metadata.

    Dynamically generates factory methods for each key defined in the schema.
    Each method returns a typed, validated key instance.
    """

    def __init__(self):
        """Initialize Redis metadata."""
        self._key_classes: Dict[str, Type[RedisKeyBase]] = {}
        self._load_keys()

    def _load_keys(self) -> None:
        """Load and register all key classes from schema."""
        self._key_classes = generate_all_keys()

        # Dynamically add factory methods
        for key_name, key_class in self._key_classes.items():
            setattr(self, key_name, self._create_factory(key_class))

    def _create_factory(self, key_class: Type[RedisKeyBase]):
        """Create a factory function for a key class.

        Args:
            key_class: The dynamically generated key class

        Returns:
            Factory function that creates instances of the key class
        """

        def factory(**kwargs) -> RedisKeyBase:
            """Factory function to create key instances.

            Args:
                **kwargs: Parameters defined in the schema for this key

            Returns:
                A validated RedisKeyBase instance

            Raises:
                ValidationError: If parameters fail validation
            """
            return key_class(**kwargs)

        # Copy class methods and other attributes from the class to the factory function
        # so they can be accessed directly, e.g., meta.quote.get_pattern()
        factory.get_pattern = key_class.get_pattern
        factory.get_prefix = key_class.get_prefix
        factory.parse = key_class.parse
        factory.__doc__ = key_class.__doc__
        factory.__name__ = key_class.__name__

        return factory

    def reload(self) -> None:
        """Reload schema and regenerate all key classes.

        Useful in development for hot-reloading schema changes.
        """
        reload_schema()
        self._load_keys()

    def get_available_keys(self) -> list[str]:
        """Get list of available key names for this service."""
        return list(self._key_classes.keys())

    def __repr__(self) -> str:
        """Developer representation."""
        keys_list = ", ".join(self.get_available_keys())
        return f"RedisMeta(keys=[{keys_list}])"


# Global instance
meta = RedisMeta()
