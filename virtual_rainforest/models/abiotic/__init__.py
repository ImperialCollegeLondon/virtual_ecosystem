r"""The :mod:`~virtual_rainforest.models.abiotic` module is one of the component
models of the Virtual Rainforest. It is comprised of several submodules that calculate
the microclimate for the Virtual Rainforest.

Each of the abiotic sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` submodule
  instantiates the AbioticModel class which consolidates the functionality of the
  abiotic model into a single class, which the high level functions of the
  Virtual Rainforest can then use.

* The :mod:`~virtual_rainforest.models.abiotic.constants` submodule provides a
  set of dataclasses containing the constants required by the broader abiotic model.

"""  # noqa: D205, D415

from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel  # noqa: F401
