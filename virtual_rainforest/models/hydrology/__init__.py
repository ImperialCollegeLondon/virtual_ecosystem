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

* The :mod:`~virtual_rainforest.models.hydrology.above_ground` submodule contains
  functions to simulate the above-ground hydrological processes for the Virtual
  Rainforest. At the moment, this includes rainwater interception by the canopy, soil
  evaporation, and all functions related to surface runoff.

* The :mod:`~virtual_rainforest.models.hydrology.below_ground` submodule contains
  functions to simulate the below-ground hydrological processes for the Virtual
  Rainforest. At the moment, this includes vertical flow and soil moisture. In the
  future, this will also include sub-surface horizontal flow.

* The :mod:`~virtual_rainforest.models.hydrology.constants` submodule contains
  parameters and constants for the hydrology model. This is a temporary solution.
"""  # noqa: D205, D415

from virtual_rainforest.core.base_model import register_model
from virtual_rainforest.models.hydrology.hydrology_model import HydrologyModel

register_model(__name__, HydrologyModel)
