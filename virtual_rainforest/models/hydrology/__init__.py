r"""The :mod:`~virtual_rainforest.models.hydrology` model is one of the component
models of the Virtual Rainforest. It is comprised of several submodules that calculate
the hydrology for the Virtual Rainforest.

Each of the hydrology sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.hydrology.hydrology_model` submodule
  instantiates the HydrologyModel class which consolidates the functionality of the
  hydrology module into a single class, which the high level functions of the
  Virtual Rainforest can then use. At the momemnt, the model calculates the hydrology
  loosely based on the SPLASH model :cite:p:`davis_simple_2017`. In the future, this
  simple bucket-model will be replaced by a process-based model that calculates a within
  grid cell water balance as well as the catchment water balance on a daily time step.

* The :mod:`~virtual_rainforest.models.hydrology.hydrology_constants` submodule contains
  parameters and constants for the hydrology model. This is a temporary solution.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.hydrology.hydrology_model import HydrologyModel

with resources.path(
    "virtual_rainforest.models.hydrology", "hydrology_schema.json"
) as schema_file_path:
    register_schema(
        module_name=HydrologyModel.model_name, schema_file_path=schema_file_path
    )
