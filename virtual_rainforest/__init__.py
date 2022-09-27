import logging

# Import all module schema here to ensure that they are added to the registry
from virtual_rainforest.core import schema  # noqa
from virtual_rainforest.plants import schema  # noqa

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(module)s - %(funcName)s(%(lineno)d) - %(message)s",
)

loggers = logging.getLogger(__name__)
