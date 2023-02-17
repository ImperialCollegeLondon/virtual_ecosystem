# noqa: D205, D415
from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.animals.animal_model import AnimalModel  # noqa: F401

with resources.path(
    "virtual_rainforest.models.animals", "animals_schema.json"
) as schema_file_path:
    register_schema(module_name="animal", schema_file_path=schema_file_path)
