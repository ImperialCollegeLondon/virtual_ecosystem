import json

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

    with open("virtual_rainforest/core/core_schema.json") as f:
        config_schema = json.load(f)

    return config_schema
