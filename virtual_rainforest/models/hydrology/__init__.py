r"""The :mod:`~virtual_rainforest.models.hydrology` model is one of the component
models of the Virtual Rainforest. It is comprised of several submodules that calculate
the hydrology for the Virtual Rainforest.

Each of the hydrology sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.hydrology.hydrology_model` submodule
  instantiates the HydrologyModel class which consolidates the functionality of the
  hydrology module into a single class, which the high level functions of the
  Virtual Rainforest can then use.

* The :mod:`~virtual_rainforest.models.hydrology.above_ground` submodule contains
  functions to simulate the above-ground hydrological processes for the Virtual
  Rainforest. At the moment, this includes rain water interception by the canopy, soil
  evaporation, and functions related to surface runoff, bypass flow, and river
  discharge.

* The :mod:`~virtual_rainforest.models.hydrology.below_ground` submodule contains
  functions to simulate the below-ground hydrological processes for the Virtual
  Rainforest. At the moment, this includes vertical flow, soil moisture and
  matric potential, groundwater storage, and subsurface horizontal flow.

* The :mod:`~virtual_rainforest.models.hydrology.constants` submodule contains
  parameters and constants for the hydrology model. This is a temporary solution.
"""  # noqa: D205, D415

from virtual_rainforest.models.hydrology.hydrology_model import (  # noqa: F401
    HydrologyModel,
)
