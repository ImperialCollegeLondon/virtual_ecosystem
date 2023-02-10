import importlib.metadata
import pkgutil
from importlib import import_module

import virtual_rainforest.models as vfm

# Import the core schema to register it
from virtual_rainforest.core import schema  # noqa: F401

# Autodiscover models in the models module to add their schema and BaseModel subclass
for module_info in pkgutil.iter_modules(vfm.__path__):
    import_module(f"virtual_rainforest.models.{module_info.name}")

__version__ = importlib.metadata.version("virtual_rainforest")
