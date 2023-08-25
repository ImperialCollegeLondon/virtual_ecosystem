"""The :mod:`~virtual_rainforest.models.plants` module provides a plants model for use
in the Virtual Rainforest. The submodules provide:

* The :mod:`~virtual_rainforest.models.plants.plants_model` submodule provides the
  PlantsModel class as the main API for interacting with the plants model.
* The :mod:`~virtual_rainforest.models.plants.constants` submodule provides dataclasses
  containing constants used in the model.
* The :mod:`~virtual_rainforest.models.plants.community` submodule provides the
  PlantCohort dataclass that records the details of an individual cohort and the Plants
  class that records list of plant cohorts by grid cell.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.plants.plants_model import PlantsModel

with resources.path(
    "virtual_rainforest.models.plants", "plants_schema.json"
) as schema_file_path:
    register_schema(
        module_name=PlantsModel.model_name, schema_file_path=schema_file_path
    )
