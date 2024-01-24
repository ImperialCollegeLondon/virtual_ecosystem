"""This submodule contains a dataclass used to generate core common components required
by models. It is used as input to the
:class:`~virtual_rainforest.core.base_model.BaseModel`, allowing single instances of
these components to be cascaded down to individual model subclass instances via the
``__init__`` method of the base model..
"""  # noqa: D205, D415

from __future__ import annotations

from dataclasses import InitVar, dataclass, field

import numpy as np
from pint import Quantity

from virtual_rainforest.core.config import Config
from virtual_rainforest.core.constants_class import ConstantsDataclass
from virtual_rainforest.core.constants_loader import load_constants
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER


@dataclass
class CoreComponents:
    """Core model components.

    This dataclass takes a validated model configuration and uses it to generate a set
    of core model attributes, populated via the ``__init__`` method of
    :class:`~virtual_rainforest.core.base_model.BaseModel` and hence inherited by the
    specific model subclasses.
    """

    layer_structure: LayerStructure = field(init=False)
    update_interval: Quantity = field(init=False)
    core_constants: ConstantsDataclass = field(init=False)
    config: InitVar[Config]

    def __post_init__(self, config: Config) -> None:
        """Populate the core components from the config."""
        self.layer_structure = LayerStructure(config=config)
        self.update_interval = "1 cneturion"
        self.core_constants = load_constants(config, "core", "CoreConsts")


@dataclass
class LayerStructure:
    """Simulation vertical layer structure.

    This data class is a container for five configurable elements used to define the
    vertical layer structure of the simulation. All are configured via the
    ``core.layers`` configuration section.
    """

    canopy_layers: int = field(init=False)
    """The maximum number of canopy layers."""
    soil_layers: list[float] = field(init=False)
    """A list of the depths of soil layer boundaries."""
    above_canopy_height_offset: float = field(init=False)
    """The height above the canopy of the provided reference climate variables."""
    surface_layer_height: float = field(init=False)
    """The height above ground used to represent surface conditions."""
    subcanopy_layer_height: float = field(init=False)
    """The height above ground used to represent subcanopy conditions."""
    layer_roles: tuple[str, ...] = field(init=False)
    """An ordered tuple giving the roles of the layers within the model."""
    config: InitVar[Config]
    """A validated model configuration."""

    def __post_init__(self, config: Config) -> None:
        """Configure a LayerStructure object.

        This is a factory method to generate a LayerStructure instance from an existing
        :class:`~virtual_rainforest.core.config.Config` instance.

        Args:
            config: A Config instance.
        """

        lyr_config = config["core"]["layers"]

        self.canopy_layers = lyr_config["canopy_layers"]
        self.soil_layers = lyr_config["soil_layers"]
        self.above_canopy_height_offset = lyr_config["above_canopy_height_offset"]
        self.surface_layer_height = lyr_config["surface_layer_height"]
        self.subcanopy_layer_height = lyr_config["subcanopy_layer_height"]
        self.layer_roles = set_layer_roles(
            canopy_layers=lyr_config["canopy_layers"],
            soil_layers=lyr_config["soil_layers"],
        )


def set_layer_roles(
    canopy_layers: int = 10, soil_layers: list[float] = [-0.5, -1.0]
) -> tuple[str, ...]:
    """Create a list of layer roles.

    This function creates a list of strings describing the layer roles for the vertical
    dimension of the Virtual Rainforest. These roles are used with data arrays that have
    that vertical dimension: the roles then show what information is being captured at
    different heights through that vertical dimension. Within the model, ground level is
    at height 0 metres: above ground heights are positive and below ground heights are
    negative. At present, models are expecting two soil layers: the top layer being
    where microbial activity happens (usually around 0.5 metres below ground) and the
    second layer where soil temperature equals annual mean air temperature (usually
    around 1 metre below ground).

    There are five layer roles capture data:

    * ``above``:  at ~2 metres above the top of the canopy.
    * ``canopy``: within each canopy layer. The maximum number of canopy layers is set
      by the ``canopy_layers`` argument and is a configurable part of the model. The
      heights of these layers are modelled from the plant community data.
    * ``subcanopy``: at ~1.5 metres above ground level.
    * ``surface``: at ~0.1 metres above ground level.
    * ``soil``: at fixed depths within the soil. These depths are set in the
      ``soil_layers`` argument and are a configurable part of the model.

    With the default values, this function gives the following layer roles.

    .. csv-table::
        :header: "Index", "Role", "Description"
        :widths: 5, 10, 30

        0, "above", "Canopy top height + 2 metres"
        1, "canopy", "Height of top of the canopy (1)"
        "...", "canopy", "Height of canopy layer ``i``"
        10, "canopy", "Height of the bottom canopy layer (10)"
        11, "subcanopy", "1.5 metres above ground level"
        12, "surface", "0.1 metres above ground level"
        13, "soil", "First soil layer at -0.5 metres"
        14, "soil", "First soil layer at -1.0 metres"

    Args:
        canopy_layers: the number of canopy layers
        soil_layers: a list giving the depth of each soil layer as a sequence of
            negative and strictly decreasing values.

    Raises:
        InitialisationError: If the number of canopy layers is not a positive
            integer or the soil depths are not a list of strictly decreasing, negative
            float values.

    Returns:
        A tuple of vertical layer role names
    """

    # sanity checks for soil and canopy layers
    if not isinstance(soil_layers, list):
        to_raise = InitialisationError(
            "The soil layers must be a list of layer depths."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if len(soil_layers) < 1:
        to_raise = InitialisationError(
            "The number of soil layers must be greater than zero."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if not all([isinstance(v, (float, int)) for v in soil_layers]):
        to_raise = InitialisationError("The soil layer depths are not all numeric.")
        LOGGER.error(to_raise)
        raise to_raise

    np_soil_layer = np.array(soil_layers)
    if not (np.all(np_soil_layer < 0) and np.all(np.diff(np_soil_layer) < 0)):
        to_raise = InitialisationError(
            "Soil layer depths must be strictly decreasing and negative."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if not isinstance(canopy_layers, int) and not (
        isinstance(canopy_layers, float) and canopy_layers.is_integer()
    ):
        to_raise = InitialisationError("The number of canopy layers is not an integer.")
        LOGGER.error(to_raise)
        raise to_raise

    if canopy_layers < 1:
        to_raise = InitialisationError(
            "The number of canopy layer must be greater than zero."
        )
        LOGGER.error(to_raise)
        raise to_raise

    layer_roles = tuple(
        ["above"]
        + ["canopy"] * int(canopy_layers)
        + ["subcanopy"]
        + ["surface"]
        + ["soil"] * len(soil_layers)
    )
    return layer_roles
