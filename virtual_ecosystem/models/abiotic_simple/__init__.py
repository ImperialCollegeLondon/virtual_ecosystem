r"""The :mod:`~virtual_ecosystem.models.abiotic_simple` module is one of the component
models of the Virtual Ecosystem. It is comprised of several submodules that calculate
the microclimate for the Virtual Ecosystem.

Each of the abiotic simple sub-modules has its own API reference page:

* The :mod:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model` submodule
  instantiates the AbioticSimpleModel class which consolidates the functionality of the
  abiotic simple module into a single class, which the high level functions of the
  Virtual Ecosystem can then use.

* The :mod:`~virtual_ecosystem.models.abiotic_simple.microclimate_simple` submodule
  contains a set functions and parameters that are used to calculate atmospheric
  temperature, relative humidity, vapour pressure deficit, wind speed, :math:`\ce{CO2}`,
  and atmospheric pressure profiles as well as soil temperature profiles.

* The :mod:`~virtual_ecosystem.models.abiotic_simple.constants` submodule provides a
  set of dataclasses containing the constants required by the broader abiotic model
  including the regression parameters for deriving vertical profiles.

"""  # noqa: D205

from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (  # noqa: F401
    AbioticSimpleModel,
)
