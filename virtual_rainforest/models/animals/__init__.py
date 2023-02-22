"""The :mod:`~virtual_rainforest.models.animal` module is one of the component models
of the Virtual Rainforest. It is comprised of a number of submodules.

Each of the animal sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.soil.animal_model` submodule instantiates the
  AnimalModel class which consolidates the functionality of the animal module
  into a single class, which the high level functions of the Virtual Rainforest
  can then make use of.
* The :mod:`~virtual_rainforest.models.soil.carcasses` provides a model for the surface
carcasses.
* The :mod:`~virtual_rainforest.models.soil.constants` provides a set of dataclasses
  containing the constants required by the broader animal model. (to come)
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.animals.animal_model import AnimalModel  # noqa: F401

with resources.path(
    "virtual_rainforest.models.animals", "animals_schema.json"
) as schema_file_path:
    register_schema(module_name="animal", schema_file_path=schema_file_path)
