r"""The :mod:`~virtual_ecosystem.models.abiotic` module is one of the component
models of the Virtual Ecosystem. It is comprised of several submodules that calculate
the microclimate for the Virtual Ecosystem.

Each of the abiotic sub-modules has its own API reference page:

* The :mod:`~virtual_ecosystem.models.abiotic.abiotic_model` submodule
  instantiates the AbioticModel class which consolidates the functionality of the
  abiotic model into a single class, which the high level functions of the
  Virtual Ecosystem can then use.

* The :mod:`~virtual_ecosystem.models.abiotic.constants` submodule provides a
  set of dataclasses containing the constants required by the broader abiotic model.

* The :mod:`~virtual_ecosystem.models.abiotic.abiotic_tools` submodule contains a set
  of general functions that are shared across submodules in the
  :mod:`~virtual_ecosystem.models.abiotic` model.

* The :mod:`~virtual_ecosystem.models.abiotic.wind` submodule calculates the
  above- and within-canopy wind profiles for the Virtual Ecosystem. These profiles will
  determine the exchange of heat, water, and :math:`\ce{CO_{2}}` between soil and
  atmosphere below the canopy as well as the exchange with the atmsophere above the
  canopy.

* The :mod:`~virtual_ecosystem.models.abiotic.energy_balance` submodule calculates the
  energy balance of the Virtual Ecosystem. The module returns vertical profiles of air
  temperature, relative humidity, and vapour pressure deficit as well as the partitioned
  energy and radiation fluxes at the leaf surface.

* The :mod:`~virtual_ecosystem.models.abiotic.soil_energy_balance` submodule calculates
  the soil energy balance of the Virtual Ecosystem. The module returns vertical
  profiles of soil temperature and the partitioned energy and radiation fluxes at the
  surface.

* The :mod:`~virtual_ecosystem.models.abiotic.conductivities` submodule calculates
  the conductivities for the energy balance of the Virtual Ecosystem. Conductivities
  describe how well heat or vapour are transferred by a medium such as air, water, or
  leaves in mol m-2 s-1. We consider heat conductivity by turbulent convection in air,
  leaf-air heat conductivity, and leaf-air vapour conductivity.
"""  # noqa: D205

from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel  # noqa: F401
