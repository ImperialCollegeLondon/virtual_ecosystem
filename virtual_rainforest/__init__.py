import importlib.metadata
import pkgutil
from importlib import import_module

# Autodiscover models in the models module
import virtual_rainforest.models as vfm

for module_info in pkgutil.iter_modules(vfm.__path__):
    import_module(f"virtual_rainforest.models.{module_info.name}")

__version__ = importlib.metadata.version("virtual_rainforest")
