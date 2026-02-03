#!/usr/bin/env python3
"""Validate that Redis stub files are up-to-date.

Used in CI/CD or development startup to ensure stubs match the schema.
"""

import sys
from pathlib import Path

import yaml


def check_stub_sync() -> bool:
    """Check if stub file is in sync with redis-meta.yml.

    Returns:
        True if in sync, False otherwise
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

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

    # Check if files exist
    if not meta_yml_path.exists():
        print(f"❌ {meta_yml_path} not found", file=sys.stderr)
        return False

    if not stub_path.exists():
        print(f"❌ {stub_path} not found", file=sys.stderr)
        print("   Run: python scripts/generate_redis_stubs.py", file=sys.stderr)
        return False

    # Load schema
    with open(meta_yml_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Read stub content
    stub_content = stub_path.read_text(encoding="utf-8")

    # Check all keys exist in stub
    keys = schema.get("keys", {}).keys()
    channels = schema.get("channels", {}).keys()

    missing_keys = []
    for key in keys:
        if f"{key}: _RedisKeyBuilder" not in stub_content:
            missing_keys.append(key)

    missing_channels = []
    for channel in channels:
        if f"{channel}: _ChannelBuilder" not in stub_content:
            missing_channels.append(channel)

    # Check for extra keys in stub (removed from yml)
    for line in stub_content.split("\n"):
        line = line.strip()
        if ": _RedisKeyBuilder" in line:
            key_name = line.split(":")[0].strip()
            if key_name not in keys:
                print(f"⚠️  Extra key in stub (removed from yml): {key_name}")

    if missing_keys or missing_channels:
        print("❌ Stub file is out of sync!", file=sys.stderr)
        if missing_keys:
            print(f"   Missing keys: {', '.join(missing_keys)}", file=sys.stderr)
        if missing_channels:
            print(
                f"   Missing channels: {', '.join(missing_channels)}", file=sys.stderr
            )
        print("   Run: python scripts/generate_redis_stubs.py", file=sys.stderr)
        return False

    print("✅ Stub file is up-to-date")
    return True


def main():
    """Main entry point."""
    if not check_stub_sync():
        sys.exit(1)


if __name__ == "__main__":
    main()
