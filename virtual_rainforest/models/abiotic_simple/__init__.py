r"""The :mod:`~virtual_rainforest.models.abiotic_simple` module is one of the component
models of the Virtual Rainforest. It is comprised of several submodules that calculate
the microclimate for the Virtual Rainforest.

Each of the abiotic sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model` submodule
  instantiates the AbioticSimpleModel class which consolidates the functionality of the
  abiotic simple module into a single class, which the high level functions of the
  Virtual Rainforest can then use.

* The :mod:`~virtual_rainforest.models.abiotic_simple.microclimate` submodule
  contains a set functions and parameters that are used to calculate atmospheric
  temperature, humidity, :math:`\ce{CO2}`, and atmospheric pressure profiles as well as
  soil temperature profiles.

"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)

with resources.path(
    "virtual_rainforest.models.abiotic_simple", "abiotic_simple_schema.json"
) as schema_file_path:
    register_schema(
        module_name=AbioticSimpleModel.model_name, schema_file_path=schema_file_path
    )
