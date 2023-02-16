from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel  # noqa: F401

with resources.path(
    "virtual_rainforest.models.abiotic", "abiotic_schema.json"
) as schema_file_path:
    register_schema(module_name="abiotic", schema_file_path=schema_file_path)
