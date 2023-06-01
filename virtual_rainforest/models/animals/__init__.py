"""The :mod:`~virtual_rainforest.models.animals` module is one of the component models
of the Virtual Rainforest. It is comprised of a number of submodules.

Each of the animal sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.animals.animal_model` submodule instantiates the
  AnimalModel class which consolidates the functionality of the animal module
  into a single class, which the high level functions of the Virtual Rainforest
  can then make use of.
* The :mod:`~virtual_rainforest.models.animals.animal_communities` provides a class for
  containing and managing all of the animal cohorts within a grid square.
* The :mod:`~virtual_rainforest.models.animals.animal_cohorts` provides a class for the
  individual animal cohorts, their attributes, and behaviors.
* The :mod:`~virtual_rainforest.models.animals.functional_group` provides a class for
  the animal functional groups that define the type of animal in an animal cohort.
* The :mod:`~virtual_rainforest.models.animals.scaling_functions` provides a set of
  allometric scaling functions that define the biological rates used in the animal
  module.
* The :mod:`~virtual_rainforest.models.animals.constants` provides a set of dataclasses
  containing the constants required by the broader animal model.
* The :mod:`~virtual_rainforest.models.animals.carcasses` provides a model for the
  surface carcasses created by mortality.
* The :mod:`~virtual_rainforest.models.animals.dummy_plants_and_soil` provides a set of
  classes defining toy implementations of soil and plant models that aid development of
  the animal module.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.animals.animal_model import AnimalModel

with resources.path(
    "virtual_rainforest.models.animals", "animals_schema.json"
) as schema_file_path:
    register_schema(
        module_name=AnimalModel.model_name, schema_file_path=schema_file_path
    )
