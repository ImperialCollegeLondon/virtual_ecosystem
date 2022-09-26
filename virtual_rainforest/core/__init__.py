from virtual_rainforest.core.config import register_schema


# This is definitely a bit questionable, its basically here to make sure that the plants
# module is imported somewhere when tests are run, this ensures that the plant schema is
# added to testing. I don't think this is the best or right way to do something like
# this, but couldn't come up with a better way to do it
# TODO - Think of a better solution for this
def load_plants_schema():
    """Imports the plants module schema."""
    from virtual_rainforest.plants import schema

    return schema


load_plants_schema()


@register_schema("core")
def schema():
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
                            },
                            "modules": {
                                "description": "List of modules to be configured",
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["grid", "modules"],
                    }
                },
                "required": ["core"],
            }
        },
        "required": ["config"],
    }

    return config_schema
