import importlib.metadata
import pkgutil
from importlib import import_module

import virtual_rainforest.models as vfm

# Import the core module schema to register the schema
import_module("virtual_rainforest.core")

# Autodiscover models in the models module to add their schema and BaseModel subclass
# All modules within virtual_rainforest.model are expected to:
# - import their BaseModel subclass to the module root, for example:
#   from virtual_rainforest.models.soil.model import SoilModel  # noqa: F401
# - register their configuration schema using core.config.register_schema
for module_info in pkgutil.iter_modules(vfm.__path__):
    import_module(f"virtual_rainforest.models.{module_info.name}")

__version__ = importlib.metadata.version("virtual_rainforest")
