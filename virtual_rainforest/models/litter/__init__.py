"""The :mod:`~virtual_rainforest.models.litter` module is one of the component models of
the Virtual Rainforest. It is comprised of a number of submodules.

Each of the litter sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.litter.litter_model` submodule instantiates the
  LitterModel class which consolidates the functionality of the litter model into a
  single class, which the high level functions of the Virtual Rainforest can then make
  use of.
* The :mod:`~virtual_rainforest.models.litter.litter_pools` provides the set of litter
  pools that the litter model is comprised of.
* The :mod:`~virtual_rainforest.models.litter.constants` provides a set of dataclasses
  containing the constants required by the broader litter model.
"""  # noqa: D205, D415

from virtual_rainforest import AUTODISCOVER
from virtual_rainforest.core.base_model import register_model
from virtual_rainforest.models.litter.litter_model import LitterModel

if AUTODISCOVER:
    register_model(__name__, LitterModel)
