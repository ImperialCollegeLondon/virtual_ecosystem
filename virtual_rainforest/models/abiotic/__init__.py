"""The :mod:`~virtual_rainforest.models.abiotic` module is one of the component models
of the Virtual Rainforest. It is comprised of several submodules that calculate the
radiation balance, the energy balance, the water balance and the atmospheric CO2
balance.

Each of the abiotic sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` submodule instantiates the
  AbioticModel class which consolidates the functionality of the abiotic module into a
  single class, which the high level functions of the Virtual Rainforest can then use.

* The :mod:`~virtual_rainforest.models.abiotic.radiation` submodule instantiates
  the :class:`~virtual_rainforest.models.abiotic.radiation.Radiation` class. This class
  calculates the radiation balance of the Virtual Rainforest.

* The :mod:`~virtual_rainforest.models.abiotic.energy_balance` submodule instantiates
  the :class:`~virtual_rainforest.models.abiotic.energy_balance.EnergyBalance` class.
  This class calculates the energy balance of the Virtual Rainforest.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel  # noqa: F401

with resources.path(
    "virtual_rainforest.models.abiotic", "abiotic_schema.json"
) as schema_file_path:
    register_schema(module_name="abiotic", schema_file_path=schema_file_path)
