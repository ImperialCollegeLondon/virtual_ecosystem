"""The :mod:`~virtual_rainforest.models.soil` module is one of the component models of
the Virtual Rainforest. It is comprised of a number of submodules.

Each of the soil sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.soil.soil_model` submodule instantiates the
  SoilModel class which consolidates the functionality of the soil module into a single
  class, which the high level functions of the Virtual Rainforest can then make use of.
* The :mod:`~virtual_rainforest.models.soil.carbon` provides a model for the soil carbon
  cycle.
* The :mod:`~virtual_rainforest.models.soil.constants` provides a set of dataclasses
  containing the constants required by the broader soil model.
"""  # noqa: D205, D415


import json
from pathlib import Path

from virtual_rainforest.core.config import register_schema


@register_schema("soil")
def schema() -> dict:
    """Defines the schema that the soil module configuration should conform to."""

    schema_file = Path(__file__).parent.resolve() / "soil_schema.json"

    with schema_file.open() as f:
        config_schema = json.load(f)

    return config_schema
