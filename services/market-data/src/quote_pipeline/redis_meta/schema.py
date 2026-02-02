"""Redis metadata schema loader with Pydantic validation."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class KeyParam(BaseModel):
    """Parameter definition for a Redis key."""

    name: str
    type: str
    validation: Optional[str] = None
    enum: Optional[List[str]] = None


class KeyDefinition(BaseModel):
    """Definition of a Redis key pattern."""

    pattern: str
    type: str  # value, hash, set, zset, list
    codec: str = "string"
    ttl: Optional[int] = None  # milliseconds
    description: str
    params: List[KeyParam]
    fields: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    configurable_via_env: Optional[str] = None


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""

    global_prefix: str = ""


class DefaultsConfig(BaseModel):
    """Global default settings."""

    ttl: Optional[int] = None
    codec: str = "string"
    namespace_separator: str = ":"


class CompatibilityConfig(BaseModel):
    """Version compatibility settings."""

    min_version: str
    max_version: str


class MigrationEntry(BaseModel):
    """Schema migration entry."""

    version: str
    date: str
    changes: List[str]


class RedisMetaSchema(BaseModel):
    """Complete Redis metadata schema."""

    version: str
    schema_version: str
    defaults: DefaultsConfig
    environments: Dict[str, EnvironmentConfig]
    keys: Dict[str, KeyDefinition]
    channels: Optional[Dict[str, Any]] = None
    compatibility: CompatibilityConfig
    migrations: List[MigrationEntry]

    def get_key_definition(self, key_name: str) -> KeyDefinition:
        """Get a specific key definition.

        Args:
            key_name: Name of the key to retrieve

        Returns:
            KeyDefinition for the specified key

        Raises:
            ValueError: If key_name is not found in schema
        """
        if key_name not in self.keys:
            raise ValueError(f"Key '{key_name}' not found in schema")
        return self.keys[key_name]

    def get_all_key_names(self) -> list[str]:
        """Get list of all key names defined in schema."""
        return list(self.keys.keys())

    def get_environment_prefix(self, env: str) -> str:
        """Get global prefix for an environment."""
        if env not in self.environments:
            return ""
        return self.environments[env].global_prefix


class SchemaLoader:
    """Loads and caches Redis metadata schema."""

    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize schema loader.

        Args:
            schema_path: Path to redis-meta.yml. If None, searches from project root.
        """
        self._schema_path = schema_path or self._find_schema_path()
        self._schema: Optional[RedisMetaSchema] = None

    def _find_schema_path(self) -> Path:
        """Find redis-meta.yml in project structure."""
        # Start from this file and go up to find project root
        current = Path(__file__).resolve()
        for parent in current.parents:
            schema_file = parent / "config" / "redis-meta.yml"
            if schema_file.exists():
                return schema_file

        # Fallback to environment variable
        env_path = os.getenv("REDIS_META_SCHEMA_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path

        raise FileNotFoundError(
            "Could not find redis-meta.yml. "
            "Set REDIS_META_SCHEMA_PATH environment variable or "
            "ensure config/redis-meta.yml exists in project root."
        )

    def load(self, force_reload: bool = False) -> RedisMetaSchema:
        """Load schema from YAML file.

        Args:
            force_reload: Force reload from file even if cached.

        Returns:
            Validated RedisMetaSchema instance.
        """
        if self._schema is not None and not force_reload:
            return self._schema

        try:
            with open(self._schema_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self._schema = RedisMetaSchema(**data)
            return self._schema

        except Exception as e:
            raise RuntimeError(
                f"Failed to load Redis metadata schema from {self._schema_path}: {e}"
            ) from e

    def reload(self) -> RedisMetaSchema:
        """Force reload schema from file."""
        return self.load(force_reload=True)


# Global schema loader instance
_loader: Optional[SchemaLoader] = None


def get_schema_loader() -> SchemaLoader:
    """Get or create global schema loader instance."""
    global _loader
    if _loader is None:
        _loader = SchemaLoader()
    return _loader


def get_schema() -> RedisMetaSchema:
    """Get loaded schema (convenience function)."""
    return get_schema_loader().load()


def reload_schema() -> RedisMetaSchema:
    """Force reload schema from file (convenience function)."""
    return get_schema_loader().reload()
