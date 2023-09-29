"""The :mod:`~virtual_rainforest.models.plants` module provides a plants model for use
in the Virtual Rainforest. The submodules provide:

* The :mod:`~virtual_rainforest.models.plants.plants_model` submodule provides the
  PlantsModel class as the main API for interacting with the plants model.
* The :mod:`~virtual_rainforest.models.plants.constants` submodule provides dataclasses
  containing constants used in the model.
* The :mod:`~virtual_rainforest.models.plants.community` submodule provides the
  PlantCohort dataclass that records the details of an individual cohort and the
  PlantCommunities class that records list of plant cohorts by grid cell.
"""  # noqa: D205, D415


from virtual_rainforest.models.plants.plants_model import PlantsModel  # noqa: F401
