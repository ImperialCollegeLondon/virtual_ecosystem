import json
from pathlib import Path

from virtual_rainforest.core.config import register_schema


@register_schema("core")
def schema() -> dict:
    """Defines the schema that the core module configuration should conform to."""

    schema_file = Path(__file__).parent.resolve() / "core_schema.json"

    with schema_file.open() as f:
        config_schema = json.load(f)

    return config_schema
