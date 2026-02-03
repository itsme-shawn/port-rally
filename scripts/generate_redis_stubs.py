#!/usr/bin/env python3
"""Redis stub file generator.

Generates __init__.pyi file from redis-meta.yml for type hinting support.
"""

import sys
from pathlib import Path
from typing import Set

import yaml


def load_redis_meta(meta_path: Path) -> dict:
    """Load redis-meta.yml file."""
    with open(meta_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_stub_content(schema: dict) -> str:
    """Generate stub file content from schema.

    Args:
        schema: Parsed redis-meta.yml content

    Returns:
        Complete .pyi stub file content
    """
    # Extract keys and channels
    keys: Set[str] = set(schema.get("keys", {}).keys())
    channels: Set[str] = set(schema.get("channels", {}).keys())

    # Build _Meta class attributes
    meta_attrs = []
    for key in sorted(keys):
        meta_attrs.append(f"    {key}: _RedisKeyBuilder")
    for channel in sorted(channels):
        meta_attrs.append(f"    {channel}: _ChannelBuilder")

    meta_class_body = "\n".join(meta_attrs) if meta_attrs else "    pass"

    # Generate complete stub content
    stub_content = f'''# This is a stub file for type hinting.
# It allows static analyzers (like in an IDE) to understand the
# dynamically created attributes of the 'meta' object.
#
# NOTE: This file is auto-generated from redis-meta.yml
# DO NOT EDIT MANUALLY - run: python scripts/generate_redis_stubs.py
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
{meta_class_body}

# The global 'meta' object that is imported from this package.
meta: _Meta
'''

    return stub_content


def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Paths
    meta_yml_path = project_root / "config" / "redis-meta.yml"
    stub_path = (
        project_root
        / "services"
        / "market-data"
        / "src"
        / "quote_pipeline"
        / "redis_meta"
        / "__init__.pyi"
    )

    # Check if redis-meta.yml exists
    if not meta_yml_path.exists():
        print(f"❌ Error: {meta_yml_path} not found", file=sys.stderr)
        sys.exit(1)

    # Load schema
    print(f"📖 Loading schema from {meta_yml_path.relative_to(project_root)}")
    schema = load_redis_meta(meta_yml_path)

    # Generate stub content
    print("⚙️  Generating stub file...")
    stub_content = generate_stub_content(schema)

    # Write stub file
    stub_path.parent.mkdir(parents=True, exist_ok=True)
    stub_path.write_text(stub_content, encoding="utf-8")

    # Summary
    keys_count = len(schema.get("keys", {}))
    channels_count = len(schema.get("channels", {}))

    print(f"✅ Generated {stub_path.relative_to(project_root)}")
    print(f"   - {keys_count} keys")
    print(f"   - {channels_count} channels")


if __name__ == "__main__":
    main()
