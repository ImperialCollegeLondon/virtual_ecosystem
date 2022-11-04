import importlib.metadata

# Import all module schema here to ensure that they are added to the registry
from virtual_rainforest.core import schema  # noqa
from virtual_rainforest.plants import schema  # noqa
from virtual_rainforest.soil import schema  # noqa

__version__ = importlib.metadata.version("virtual_rainforest")
