import importlib.metadata

# Import all module schema here to ensure that they are added to the registry
from virtual_rainforest.core import schema  # noqa
from virtual_rainforest.models.abiotic import schema  # noqa
from virtual_rainforest.models.abiotic.model import AbioticModel  # noqa
from virtual_rainforest.plants import schema  # noqa
from virtual_rainforest.soil import schema  # noqa

# Import models here so that they also end up in the registry
from virtual_rainforest.soil.model import SoilModel  # noqa

__version__ = importlib.metadata.version("virtual_rainforest")
