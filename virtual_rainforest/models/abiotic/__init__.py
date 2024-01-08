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

* The :mod:`~virtual_rainforest.models.abiotic.abiotic_tools` submodule contains a set
  of general functions that are shared across submodules in the
  :mod:`~virtual_rainforest.models.abiotic` model.

* The :mod:`~virtual_rainforest.models.abiotic.wind` submodule calculates the
  above- and within-canopy wind profiles for the Virtual Rainforest. These profiles will
  determine the exchange of heat, water, and :math:`CO_{2}` between soil and atmosphere
  below the canopy as well as the exchange with the atmsophere above the canopy.

* The :mod:`~virtual_rainforest.models.abiotic.energy_balance` submodule calculates the
  energy balance of the Virtual Rainforest. The module returns vertical profiles of air
  temperature, relative humidity, and soil temperature.
"""  # noqa: D205, D415

from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel  # noqa: F401
