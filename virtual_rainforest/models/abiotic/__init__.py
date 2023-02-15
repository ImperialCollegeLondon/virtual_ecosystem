"""The :mod:`~virtual_rainforest.models.abiotic` module is one of the component models
of the Virtual Rainforest. It is comprised of several submodules that calculate the
radiation balance, the energy balance, the water balance and the atmospheric CO2
balance.

Each of the abiotic sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` submodule instantiates the
  AbioticModel class which consolidates the functionality of the abiotic module into a
  single class, which the high level functions of the Virtual Rainforest can then use.

* The :mod:`~virtual_rainforest.models.abiotic.radiation` submodule instantiates
  the :class:`~virtual_rainforest.models.abiotic.energy_balance.Radiation` class.

* The :mod:`~virtual_rainforest.models.abiotic.energy_balance` submodule instantiates
  the :class:`~virtual_rainforest.models.abiotic.energy_balance.EnergyBalance` class.
"""  # noqa: D205, D415

import json
from pathlib import Path

from virtual_rainforest.core.config import register_schema


@register_schema("abiotic")
def schema() -> dict:
    """Defines the schema that the abiotic module configuration should conform to."""

    schema_file = Path(__file__).parent.resolve() / "abiotic_schema.json"

    with schema_file.open() as f:
        config_schema = json.load(f)

    return config_schema
