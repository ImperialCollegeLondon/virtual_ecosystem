import json

from virtual_rainforest.core.config import register_schema


@register_schema("core")
def schema():
    """Defines the schema that the core module configuration should conform to."""

    with open("virtual_rainforest/core/core_schema.json") as f:
        config_schema = json.load(f)

    return config_schema
