from virtual_rainforest.core.config import register_schema


@register_schema("plants")
def core_schema():
    """Defines the schema that the plant module configuration should conform to."""

    config_schema = {}

    return config_schema
