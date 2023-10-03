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

* The :mod:`~virtual_rainforest.models.abiotic_simple.constants` submodule provides a
  set of dataclasses containing the constants required by the broader soil model.

"""  # noqa: D205, D415

from virtual_rainforest.core.registry import register_module
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)

register_module(module_name=__name__, model=AbioticSimpleModel)
