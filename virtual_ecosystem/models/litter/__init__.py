"""The :mod:`~virtual_ecosystem.models.litter` module is one of the component models of
the Virtual Ecosystem. It is comprised of a number of submodules.

Each of the litter sub-modules has its own API reference page:

* The :mod:`~virtual_ecosystem.models.litter.litter_model` submodule instantiates the
  LitterModel class which consolidates the functionality of the litter model into a
  single class, which the high level functions of the Virtual Ecosystem can then make
  use of.
* :mod:`~virtual_ecosystem.models.litter.carbon` provides the set of litter carbon
  pools that the litter model is comprised of.
* :mod:`~virtual_ecosystem.models.litter.chemistry` tracks the chemistry (lignin,
  nitrogen and phosphorus) of the litter pools.
* :mod:`~virtual_ecosystem.models.litter.inputs` handles the partitioning of biomass
  input between the different litter pools.
* :mod:`~virtual_ecosystem.models.litter.env_factors` provides the functions
  capturing the impact of environmental factors on litter decay.
* :mod:`~virtual_ecosystem.models.litter.constants` provides a set of dataclasses
  containing the constants required by the broader litter model.
"""  # noqa: D205

from virtual_ecosystem.models.litter.litter_model import LitterModel  # noqa: F401
