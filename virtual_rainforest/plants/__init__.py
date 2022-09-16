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


# "items": {
#                                     "prefixItems": [
#                                         {
#                                             "name": "name",
#                                             "type": "string",
#                                             "constraints": {
#                                                 "required": True,
#                                                 "unique": True,
#                                             },
#                                         },
#                                         {
#                                             "name": "maxh",
#                                             "type": "number",
#                                             "constraints": {
#                                                 "required": True,
#                                                 "minimum": 0.0,
#                                             },
#                                         },
#                                     ],
#                                     "items": False,
#                                     "unevaluatedItems": False,
#                                 }
