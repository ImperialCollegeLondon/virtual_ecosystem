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
from pint.errors import DimensionalityError, UndefinedUnitError

from virtual_rainforest.core.config import Config
from virtual_rainforest.core.constants_class import ConstantsDataclass
from virtual_rainforest.core.constants_loader import load_constants
from virtual_rainforest.core.exceptions import ConfigurationError
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
    """The vertical layer structure for the simulation."""
    model_timing: ModelTiming = field(init=False)
    """The model timing details for the simulation."""
    core_constants: ConstantsDataclass = field(init=False)
    """The core constants definitions for the simulation"""
    config: InitVar[Config]
    """A validated model configuration."""

    def __post_init__(self, config: Config) -> None:
        """Populate the core components from the config."""
        self.layer_structure = LayerStructure(config=config)
        self.model_timing = ModelTiming(config=config)
        self.core_constants = load_constants(config, "core", "CoreConsts")


@dataclass
class ModelTiming:
    """Model timing details.

    This data class defines the timing of a Virtual Rainforest simulation from the
    ``core.timing`` section of a validated model configuration. The start time, run
    length and update interval are all extracted from the configuration and validated.

    The end time is calculated from the previously extracted timing information. This
    end time will always be the largest whole multiple of the update interval that
    exceeds or equal the configured ``run_length``.


    Raises:
        ConfigurationError: If the timing configuration details are incorrect.
    """

    start_time: np.datetime64 = field(init=False)
    """The start time of the simulation."""
    end_time: np.datetime64 = field(init=False)
    """The calculated end time of the simulation."""
    reconciled_run_length: np.timedelta64 = field(init=False)
    """The difference between start and calculated end time."""
    run_length: np.timedelta64 = field(init=False)
    """The configured run length."""
    run_length_quantity: Quantity = field(init=False)
    """The configured run length as a pint Quantity."""
    update_interval: np.timedelta64 = field(init=False)
    """The configured update interval."""
    update_interval_quantity: Quantity = field(init=False)
    """The configured update interval as a pint Quantity."""
    config: InitVar[Config]
    """A validated model configuration."""

    def __post_init__(self, config: Config) -> None:
        """Populate the ``ModelTiming`` instance.

        This method populates the ``ModelTiming`` attributes from the provided
        :class:`~virtual_rainforest.core.config.Config` instance.

        Args:
            config: A Config instance.
        """

        timing = config["core"]["timing"]

        # Validate and convert configuration
        # NOTE: some of this is also trapped by validation against the core schema.
        # Start date from string to np.datetime64
        try:
            start_time = np.datetime64(timing["start_date"])
        except ValueError:
            to_raise = ConfigurationError(
                f"Cannot parse start_date: {timing['start_date']}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.start_time = start_time

        # Handle conversion of strings to time quantities
        for attr in ("run_length", "update_interval"):
            try:
                value = timing[attr]
                value_pint = Quantity(value).to("seconds")
            except (DimensionalityError, UndefinedUnitError):
                to_raise = ConfigurationError(
                    f"Invalid units for core.timing.{attr}: {value}"
                )
                LOGGER.error(to_raise)
                raise to_raise

            # Set values as timedelta64 values with second precision and store quantity
            setattr(self, attr, np.timedelta64(round(value_pint.magnitude), "s"))
            setattr(self, attr + "_quantity", value_pint)

        if self.run_length < self.update_interval:
            to_raise = ConfigurationError(
                f"Model run length ({timing['run_length']}) expires before "
                f"first update ({timing['update_interval']})"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Calculate when the simulation should stop as the first number of update
        # intervals to exceed the requested run length and calculate the actual run
        # length
        self.end_time = (
            start_time
            + np.ceil(self.run_length / self.update_interval) * self.update_interval
        )
        self.reconciled_run_length = self.end_time - self.start_time

        # Log the completed timing creation.
        LOGGER.info(
            "Timing details built from model configuration: "
            "start - %s, end - %s, run length - %s"
            % (self.start_time, self.end_time, self.reconciled_run_length)
        )


@dataclass
class LayerStructure:
    """Simulation vertical layer structure.

    This class defines the structure of the vertical dimension of the Virtual Rainforest
    from a model configuration. Five values from the ``core.layers`` configuration
    section are used to define a set of vertical layers and their heights (or relative
    heights): ``canopy_layers``, ``soil_layers``, ``above_canopy_height_offset``,
    ``surface_layer_height`` and``subcanopy_layer_height``. These values are validatated
    and then assigned to attributes of this class. The ``n_layers`` and ``layer_roles``
    attributes report the total number of layers in the vertical dimension and a tuple
    of the role of each layer within that dimension.

    The layer structure is shown below, along with values from the default
    configuration. All heights are in metres relative to ground level and the canopy
    layer heights are defined dynamically by the
    :class:`~virtual_rainforest.models.plants.PlantsModel`.

    .. csv-table::
        :header: "Index", "Role", "Description", "Set by", "Default"
        :widths: 5, 10, 30, 30, 10

        0, "above", "Above canopy conditions", "``above_ground_canopy_offset``", "+2 m"
        1, "canopy", "Height of first canopy layer",  "``PlantsModel``", "--"
        "...", "canopy", "Height of other canopy layers",  "``PlantsModel``", "--"
        10, "canopy", "Height of the last canopy layer ", "``PlantsModel``", "--"
        11, "subcanopy", "Subcanopy height", ``subcanopy_layer_height``, "1.5 m"
        12, "surface", "Near surface conditions", ``surface_layer_height``, "0.1 m"
        13, "soil", "Upper soil layer depth",  ``soil_layers``, "-0.25 m"
        14, "soil", "Lower soil layer depth",  ``soil_layers``, "-1.25 m"

    Raises:
        ConfigurationError: If the configuration elements are incorrect for defining
            the model timing.
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
        """Populate the ``LayerStructure`` instance.

        This method populates the ``LayerStructure`` attributes from the provided
        :class:`~virtual_rainforest.core.config.Config` instance.

        Args:
            config: A Config instance.
        """

        lyr_config = config["core"]["layers"]

        # Validate contents
        # NOTE: some of this is also trapped by validation against the core schema.
        # Canopy layers
        canopy_layers = lyr_config["canopy_layers"]
        if (
            not isinstance(canopy_layers, int)
            and not (isinstance(canopy_layers, float) and canopy_layers.is_integer())
            and canopy_layers < 1
        ):
            to_raise = ConfigurationError(
                "The number of canopy layers is not a positive integer."
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.canopy_layers = canopy_layers

        # Soil layers
        soil_layers = lyr_config["soil_layers"]

        if not isinstance(soil_layers, list) or len(soil_layers) < 1:
            to_raise = ConfigurationError(
                "The soil layers must be a non-empty list of layer depths."
            )
            LOGGER.error(to_raise)
            raise to_raise

        if not all([isinstance(v, (float, int)) for v in soil_layers]):
            to_raise = ConfigurationError("The soil layer depths are not all numeric.")
            LOGGER.error(to_raise)
            raise to_raise

        np_soil_layer = np.array(soil_layers)
        if not (np.all(np_soil_layer < 0) and np.all(np.diff(np_soil_layer) < 0)):
            to_raise = ConfigurationError(
                "Soil layer depths must be strictly decreasing and negative."
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.soil_layers = soil_layers

        # Other heights should all be positive floats
        for attr, value in (
            ("above_canopy_height_offset", lyr_config["above_canopy_height_offset"]),
            ("surface_layer_height", lyr_config["surface_layer_height"]),
            ("subcanopy_layer_height", lyr_config["subcanopy_layer_height"]),
        ):
            if not isinstance(value, (float, int)) or value < 0:
                to_raise = ConfigurationError(
                    f"The {attr} value must be a positive float."
                )
                LOGGER.error(to_raise)
                raise to_raise
            else:
                setattr(self, attr, value)

        self.layer_roles = tuple(
            ["above"]
            + ["canopy"] * int(canopy_layers)
            + ["subcanopy"]
            + ["surface"]
            + ["soil"] * len(soil_layers)
        )

        LOGGER.info("Layer structure built from model configuration")
