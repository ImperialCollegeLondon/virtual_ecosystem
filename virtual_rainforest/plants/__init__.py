import json

from virtual_rainforest.core.config import register_schema


@register_schema("plants")
def schema():
    """Defines the schema that the plant module configuration should conform to."""

    with open("virtual_rainforest/plants/plants_schema.json") as f:
        config_schema = json.load(f)

    return config_schema
