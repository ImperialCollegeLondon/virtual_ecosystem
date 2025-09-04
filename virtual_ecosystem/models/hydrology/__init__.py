r"""The :mod:`~virtual_ecosystem.models.hydrology` model is one of the component
models of the Virtual Ecosystem. It is comprised of several submodules that calculate
the hydrology for the Virtual Ecosystem.

Each of the hydrology sub-modules has its own API reference page:

* The :mod:`~virtual_ecosystem.models.hydrology.hydrology_model` submodule
  instantiates the HydrologyModel class which consolidates the functionality of the
  hydrology module into a single class, which the high level functions of the
  Virtual Ecosystem can then use.

* The :mod:`~virtual_ecosystem.models.hydrology.above_ground` submodule contains
  functions to simulate the above-ground hydrological processes for the Virtual
  Ecosystem. At the moment, this includes rain water interception by the canopy, canopy
  evaporation and leaf drainage, soil evaporation, and functions related to surface
  runoff, bypass flow, and river discharge.

* The :mod:`~virtual_ecosystem.models.hydrology.below_ground` submodule contains
  functions to simulate the below-ground hydrological processes for the Virtual
  Ecosystem. At the moment, this includes vertical flow, soil moisture and
  matric potential, groundwater storage, and subsurface horizontal flow.

* The :mod:`~virtual_ecosystem.models.hydrology.constants` submodule contains
  parameters and constants for the hydrology model.

* The :mod:`~virtual_ecosystem.models.hydrology.hydrology_tools` submodule
  contains a set of functions that support the data preprocessing for the model update,
  for example by preselecting relevant layers, distributing monthly rainfall over 30
  days, and so on.
"""  # noqa: D205

from virtual_ecosystem.models.hydrology.hydrology_model import (  # noqa: F401
    HydrologyModel,
)
