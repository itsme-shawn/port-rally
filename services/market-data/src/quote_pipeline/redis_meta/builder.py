"""Dynamic Redis metadata class builder."""

from typing import Any, Dict, Type

from pydantic import Field, create_model

from .models import RedisKeyBase
from .schema import KeyDefinition, get_schema


def _python_type_from_schema(type_str: str) -> Type:
    """Map schema type string to Python type."""
    type_mapping = {
        "string": str,
        "uuid": str,  # UUIDs are strings in Python
        "int": int,
        "float": float,
        "bool": bool,
    }
    return type_mapping.get(type_str, str)


def create_key_class(
    key_name: str, key_def: KeyDefinition
) -> Type[RedisKeyBase]:
    """Dynamically create a Pydantic model class for a Redis key.

    Args:
        key_name: Key name (e.g., "quote")
        key_def: Key definition from schema

    Returns:
        A new class inheriting from RedisKeyBase with typed parameters.
    """
    # Build field definitions for Pydantic
    fields: Dict[str, Any] = {}

    for param in key_def.params:
        python_type = _python_type_from_schema(param.type)

        # Create field with description
        field_kwargs = {"description": f"Parameter: {param.name}"}

        # Add validation if present
        if param.validation:
            field_kwargs["pattern"] = param.validation

        fields[param.name] = (python_type, Field(**field_kwargs))

    # Create the dynamic class
    class_name = "".join(word.capitalize() for word in key_name.split("_")) + "Key"

    KeyClass = create_model(
        class_name,
        __base__=RedisKeyBase,
        __module__=__name__,
        **fields,
    )

    # Set class variable for key name
    KeyClass.__key_name__ = key_name

    # Add a docstring
    KeyClass.__doc__ = (
        f"{key_def.description}\n\n"
        f"Pattern: {key_def.pattern}\n"
        f"Type: {key_def.type}\n"
        f"TTL: {key_def.ttl or 'None'}\n"
    )

    return KeyClass


def generate_all_keys() -> Dict[str, Type[RedisKeyBase]]:
    """Generate all key classes from schema.

    Returns:
        Dictionary mapping key names to their generated classes.
    """
    schema = get_schema()

    key_classes = {}
    for key_name, key_def in schema.keys.items():
        key_classes[key_name] = create_key_class(key_name, key_def)

    return key_classes
