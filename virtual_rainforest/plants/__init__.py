from virtual_rainforest.core.config import register_schema


@register_schema("plants")
def core_schema():
    """Defines the schema that the plant module configuration should conform to."""

    config_schema = {
        "type": "object",
        "properties": {
            "config": {
                "type": "object",
                "properties": {
                    "plants": {
                        "description": "Configuration settings for the plants module",
                        "type": "object",
                        "properties": {
                            "ftypes": {
                                "description": "Details of the plant functional types",
                                "type": "array",
                            }
                        },
                        "required": ["ftypes"],
                    }
                },
                "required": ["plants"],
            }
        },
        "required": ["config"],
    }

    return config_schema
