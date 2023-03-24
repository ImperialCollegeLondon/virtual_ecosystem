"""The :mod:`~virtual_rainforest.models.abiotic` module is one of the component models
of the Virtual Rainforest. It is comprised of several submodules that calculate the
radiation balance, the energy balance, the water balance and the atmospheric CO2
balance.

Each of the abiotic sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` submodule instantiates the
  AbioticModel class which consolidates the functionality of the abiotic module into a
  single class, which the high level functions of the Virtual Rainforest can then use.

* The :mod:`~virtual_rainforest.models.abiotic.abiotic_tools` submodule contains a set
  of general functions and universal constants that are shared across submodels in the
  :mod:`~virtual_rainforest.models.abiotic.abiotic_model` model.

* The :mod:`~virtual_rainforest.models.abiotic.radiation` submodule instantiates
  the :class:`~virtual_rainforest.models.abiotic.radiation.Radiation` class. This class
  calculates the radiation balance of the Virtual Rainforest.

* The :mod:`~virtual_rainforest.models.abiotic.wind` submodule calculates the above- and
  within-canopy wind profiles of the Virtual Rainforest. These profiles will determine
  the exchange of heat, water, and CO2 between soil and atmosphere below the canopy as
  well as the exchange with the atmsophere above the canopy.

* The :mod:`~virtual_rainforest.models.abiotic.atmospheric_co2` submodule calculates the
  above- and within-canopy CO2 concentration profiles of the Virtual Rainforest.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

with resources.path(
    "virtual_rainforest.models.abiotic", "abiotic_schema.json"
) as schema_file_path:
    register_schema(
        module_name=AbioticModel.model_name, schema_file_path=schema_file_path
    )
