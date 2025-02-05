"""The :mod:`~virtual_ecosystem.models.plants` module provides
the :class:`~virtual_ecosystem.models.plants.plants_model.PlantsModel`
implementation for use in the Virtual Ecosystem.

The main submodule is :mod:`~virtual_ecosystem.models.plants.plants_model` submodule,
which provides the :class:`~virtual_ecosystem.models.plants.plants_model.PlantsModel`
class as the main API to initialise and update the plants model.

The other submodules include:

* The :mod:`~virtual_ecosystem.models.plants.constants` submodule provides definitions
  of the main constants used in the model.

* The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule implements the
  handling of individual plant functional types and the overall flora definition to be
  used in a simulation.

* The :mod:`~virtual_ecosystem.models.plants.community` submodule implements a community
  object, defined as a the set of size-structured plant cohorts occurring in a grid
  cell.

* The :mod:`~virtual_ecosystem.models.plants.canopy` submodule implements the
  calculation of a whole cell representation of the canopy structure within a grid cell,
  given a particular plant community.
"""  # noqa: D205

from virtual_ecosystem.models.plants.plants_model import PlantsModel  # noqa: F401
