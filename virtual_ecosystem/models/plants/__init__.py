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

* The :mod:`~virtual_ecosystem.models.plants.communities` submodule provides the
  :class:`~virtual_ecosystem.models.plants.communities.PlantCommunities` class which
  maps each grid cell on to a representation of the plant community within that cell.
  Each grid cell has a single :class:`pyrealm.demography.community.Community` object
  that contains includes a :class:`pyrealm.demography.community.Cohorts` instance
  describing the size-structured cohorts of different plant functional types within the
  grid cell.

* The :mod:`~virtual_ecosystem.models.plants.canopy` submodule provides code to
  calculate the complete canopy structure across all cohorts for the plant community
  present in a particular grid cell.
"""  # noqa: D205

from virtual_ecosystem.models.plants.plants_model import PlantsModel  # noqa: F401
