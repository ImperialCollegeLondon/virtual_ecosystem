"""The :mod:`~virtual_ecosystem.models.soil` module is one of the component models of
the Virtual Ecosystem. It is comprised of a number of submodules.

Each of the soil sub-modules has its own API reference page:

* The :mod:`~virtual_ecosystem.models.soil.soil_model` submodule instantiates the
  SoilModel class which consolidates the functionality of the soil module into a single
  class, which the high level functions of the Virtual Ecosystem can then make use of.
* The :mod:`~virtual_ecosystem.models.soil.carbon` provides a model for the soil carbon
  cycle.
* The :mod:`~virtual_ecosystem.models.soil.env_factors` provides functions that capture
  the impact of environmental factors on microbial rates.
* The :mod:`~virtual_ecosystem.models.soil.constants` provides a set of dataclasses
  containing the constants required by the broader soil model.
"""  # noqa: D205, D415

from virtual_ecosystem.models.soil.soil_model import SoilModel  # noqa: F401
