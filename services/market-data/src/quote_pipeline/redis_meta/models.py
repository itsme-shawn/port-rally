"""Base model for Redis metadata."""

import re
from typing import ClassVar, Dict, Optional

from pydantic import BaseModel, ValidationError

from .schema import get_schema


class RedisKeyBase(BaseModel):
    """Base class for all Redis key instances."""

    class Config:
        frozen = True  # Make instances immutable
        arbitrary_types_allowed = True

    # Class variable for key name
    __key_name__: ClassVar[str] = ""

    def build(self, env: Optional[str] = None) -> str:
        """Build the final Redis key string.

        Args:
            env: Environment name (dev, prod, test). If None, no prefix is added.

        Returns:
            Complete Redis key string with parameters substituted.

        Raises:
            ValueError: If parameter validation fails.
        """
        schema = get_schema()
        key_def = schema.get_key_definition(self.__key_name__)

        # Start with the pattern
        key = key_def.pattern

        # Substitute each parameter
        for param in key_def.params:
            # Get the value from this instance
            if not hasattr(self, param.name):
                raise ValueError(
                    f"Missing required parameter '{param.name}' for key '{self.__key_name__}'"
                )

            value = getattr(self, param.name)

            # Validate enum if specified
            if param.enum and str(value) not in param.enum:
                raise ValueError(
                    f"Invalid value for {param.name}: {value}. "
                    f"Must be one of {param.enum}"
                )

            # Validate pattern if specified
            if param.validation:
                if not re.match(param.validation, str(value)):
                    raise ValueError(
                        f"Invalid {param.name}: {value}. "
                        f"Must match pattern: {param.validation}"
                    )

            # Replace in pattern
            key = key.replace(f"{{{param.name}}}", str(value))

        # Apply environment prefix if specified
        if env:
            prefix = schema.get_environment_prefix(env)
            if prefix:
                separator = schema.defaults.namespace_separator
                key = f"{prefix}{separator}{key}"

        return key

    @classmethod
    def get_prefix(cls) -> str:
        """Get the static part of the key before any parameters."""
        schema = get_schema()
        key_def = schema.get_key_definition(cls.__key_name__)
        separator = schema.defaults.namespace_separator
        return key_def.pattern.split(separator)[0]

    @classmethod
    def get_pattern(cls, **kwargs) -> str:
        """
        Build a key pattern for searching, with wildcards.
        Unprovided parameters will be replaced with '*'.

        Args:
            **kwargs: Specific values to substitute into the pattern.

        Returns:
            A key pattern string (e.g., "quote:KR:KOSPI:*").
        """
        schema = get_schema()
        key_def = schema.get_key_definition(cls.__key_name__)
        pattern = key_def.pattern

        for param in key_def.params:
            if param.name in kwargs:
                pattern = pattern.replace(f"{{{param.name}}}", str(kwargs[param.name]))
            else:
                pattern = pattern.replace(f"{{{param.name}}}", "*")
        return pattern

    @classmethod
    def parse(cls, key: str) -> Optional[Dict[str, str]]:
        """
        Parses a given key string against the key's pattern.

        Args:
            key: The Redis key string to parse.

        Returns:
            A dictionary of the parsed parameters, or None if it doesn't match.
        """
        schema = get_schema()
        key_def = schema.get_key_definition(cls.__key_name__)
        separator = schema.defaults.namespace_separator

        # Build a regex that is not greedy
        pattern_regex = key_def.pattern
        param_names = [p.name for p in key_def.params]

        for name in param_names:
            # Replace {param} with a named capture group that doesn't include the separator
            pattern_regex = pattern_regex.replace(
                f"{{{name}}}", f"(?P<{name}>[^{separator}]+)"
            )

        match = re.fullmatch(pattern_regex, key)

        if match:
            return match.groupdict()
        return None

    def get_ttl(self) -> Optional[int]:
        """Get TTL in milliseconds from schema.

        Returns:
            TTL in milliseconds, or None if no expiration.
        """
        schema = get_schema()
        key_def = schema.get_key_definition(self.__key_name__)
        return key_def.ttl

    def get_ttl_seconds(self) -> Optional[int]:
        """Get TTL in seconds from schema.

        Returns:
            TTL in seconds, or None if no expiration.
        """
        ttl = self.get_ttl()
        return ttl // 1000 if ttl is not None else None

    def get_type(self) -> str:
        """Get Redis data type (value, hash, set, etc.)."""
        schema = get_schema()
        key_def = schema.get_key_definition(self.__key_name__)
        return key_def.type

    def get_codec(self) -> str:
        """Get codec type (string, json, etc.)."""
        schema = get_schema()
        key_def = schema.get_key_definition(self.__key_name__)
        return key_def.codec

    def get_fields(self) -> Optional[list[str]]:
        """Get expected fields for hash types."""
        schema = get_schema()
        key_def = schema.get_key_definition(self.__key_name__)
        return key_def.fields

    def __str__(self) -> str:
        """String representation (builds key without env prefix)."""
        return self.build()

    def __repr__(self) -> str:
        """Developer representation."""
        params = {
            field: getattr(self, field)
            for field in self.model_fields
            if not field.startswith("_")
        }
        return f"{self.__class__.__name__}({params})"
