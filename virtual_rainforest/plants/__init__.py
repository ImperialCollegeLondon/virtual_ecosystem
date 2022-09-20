from virtual_rainforest.core.config import register_schema


@register_schema("plants")
def schema():
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
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "pft_name": {"type": "string"},
                                        "maxh": {
                                            "type": "number",
                                            "exclusiveMinimum": 0.0,
                                        },
                                    },
                                    "required": ["pft_name", "maxh"],
                                },
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
