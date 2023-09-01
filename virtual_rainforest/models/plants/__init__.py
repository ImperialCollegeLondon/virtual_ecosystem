from importlib import resources

from virtual_rainforest.core.config import register_schema

with resources.path(
    "virtual_rainforest.models.plants", "model_schema.json"
) as schema_file_path:
    register_schema(module_name="plants", schema_file_path=schema_file_path)
