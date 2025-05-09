"""The base initialisation of the Virtual Ecosystem model."""

import importlib.metadata
import warnings

from pyrealm.core.experimental import ExperimentalFeatureWarning

from . import example_data

__version__ = importlib.metadata.version("virtual_ecosystem")

example_data_path = example_data.__path__[0]
"""The path to the example data folder.

Note that you will not be able to load data from this folder under certain
circumstances, e.g. if this Python package is inside a zip file, but it should work in
the ordinary case.
"""

# Ignore experimental and user warnings coming from pyrealm

warnings.filterwarnings(
    action="ignore", category=ExperimentalFeatureWarning, module=r"pyrealm"
)
warnings.filterwarnings(action="ignore", category=UserWarning, module=r"pyrealm")
