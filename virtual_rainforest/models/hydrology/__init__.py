r"""The :mod:`~virtual_rainforest.models.hydrology` module is one of the component
models of the Virtual Rainforest. It is comprised of several submodules that calculate
the hydrology for the Virtual Rainforest, currently loosely based on the SPLASH model
:cite:p:`davis_simple_2017`.

"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.hydrology.hydrology_model import HydrologyModel

with resources.path(
    "virtual_rainforest.models.hydrology", "hydrology.json"
) as schema_file_path:
    register_schema(
        module_name=HydrologyModel.model_name, schema_file_path=schema_file_path
    )
