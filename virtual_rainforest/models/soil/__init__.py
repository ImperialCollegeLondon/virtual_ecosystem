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

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.soil.soil_model import SoilModel

with resources.path(
    "virtual_rainforest.models.soil", "soil_schema.json"
) as schema_file_path:
    register_schema(module_name=SoilModel.model_name, schema_file_path=schema_file_path)
