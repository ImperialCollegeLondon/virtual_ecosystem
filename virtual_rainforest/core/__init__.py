from virtual_rainforest.core.config import register_schema


@register_schema("core")
def core_schema():
    """Defines the schema that the core module configuration should conform to."""

    config_schema = {
        "type": "object",
        "properties": {
            "config": {
                "type": "object",
                "properties": {
                    "core": {
                        "description": "Configuration settings for the core module",
                        "type": "object",
                        "properties": {
                            "grid": {
                                "description": "Details of the grid to configure",
                                "type": "object",
                                "properties": {
                                    "nx": {
                                        "description": "Number of grid cells in x "
                                        "direction",
                                        "type": "integer",
                                        "exclusiveMinimum": 0,
                                    },
                                    "ny": {
                                        "description": "Number of grid cells in y "
                                        "direction",
                                        "type": "integer",
                                        "exclusiveMinimum": 0,
                                    },
                                },
                                "required": ["nx", "ny"],
                                "additionalProperties": False,
                            },
                            "modules": {
                                "description": "List of modules to be configured",
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["grid", "modules"],
                        "additionalProperties": False,
                    }
                },
                "required": ["core"],
                "additionalProperties": False,
            }
        },
        "required": ["config"],
        "additionalProperties": False,
    }

    return config_schema
