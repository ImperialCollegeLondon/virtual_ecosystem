"""The :mod:`~virtual_rainforest.models.abiotic_simple` module is one of the component
models of the Virtual Rainforest.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
    AbioticSimpleModel,
)

with resources.path(
    "virtual_rainforest.models.abiotic_simple", "abiotic_simple_schema.json"
) as schema_file_path:
    register_schema(
        module_name=AbioticSimpleModel.model_name, schema_file_path=schema_file_path
    )
