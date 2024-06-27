"""This submodule contains a dataclass used to generate core common components required
by models. It is used as input to the
:class:`~virtual_ecosystem.core.base_model.BaseModel`, allowing single instances of
these components to be cascaded down to individual model subclass instances via the
``__init__`` method of the base model..
"""  # noqa: D205

from __future__ import annotations

from dataclasses import InitVar, dataclass, field

import numpy as np
from numpy.typing import NDArray
from pint import Quantity
from pint.errors import DimensionalityError, UndefinedUnitError
from xarray import DataArray

from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER


@dataclass
class CoreComponents:
    """Core model components.

    This dataclass takes a validated model configuration and uses it to generate a set
    of core model attributes, populated via the ``__init__`` method of
    :class:`~virtual_ecosystem.core.base_model.BaseModel` and hence inherited by the
    specific model subclasses.
    """

    grid: Grid = field(init=False)
    """A grid structure for the simulation."""
    layer_structure: LayerStructure = field(init=False)
    """The vertical layer structure for the simulation."""
    model_timing: ModelTiming = field(init=False)
    """The model timing details for the simulation."""
    core_constants: CoreConsts = field(init=False)
    """The core constants definitions for the simulation"""
    config: InitVar[Config]
    """A validated model configuration."""

    def __post_init__(self, config: Config) -> None:
        """Populate the core components from the config."""
        self.grid = Grid.from_config(config=config)
        self.core_constants = load_constants(config, "core", "CoreConsts")
        self.layer_structure = LayerStructure(
            config=config,
            n_cells=self.grid.n_cells,
            max_depth_of_microbial_activity=self.core_constants.max_depth_of_microbial_activity,
        )
        self.model_timing = ModelTiming(config=config)


@dataclass
class ModelTiming:
    """Model timing details.

    This data class defines the timing of a Virtual Ecosystem simulation from the
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
    n_updates: int = field(init=False)
    """The total number of model updates in the configured run."""
    config: InitVar[Config]
    """A validated model configuration."""

    def __post_init__(self, config: Config) -> None:
        """Populate the ``ModelTiming`` instance.

        This method populates the ``ModelTiming`` attributes from the provided
        :class:`~virtual_ecosystem.core.config.Config` instance.

        Args:
            config: A Config instance.
        """

        timing = config["core"]["timing"]

        # Validate and convert configuration
        # NOTE: some of this is also trapped by validation against the core schema.
        # Start date from string to np.datetime64
        try:
            self.start_time = np.datetime64(timing["start_date"])
        except ValueError:
            to_raise = ConfigurationError(
                f"Cannot parse start_date: {timing['start_date']}"
            )
            LOGGER.error(to_raise)
            raise to_raise

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
            self.start_time
            + np.ceil(self.run_length / self.update_interval) * self.update_interval
        )
        self.reconciled_run_length = self.end_time - self.start_time

        self.n_updates = int((self.end_time - self.start_time) / self.update_interval)

        # Log the completed timing creation.
        LOGGER.info(
            "Timing details built from model configuration: "  # noqa: UP032
            "start - {}, end - {}, run length - {}".format(
                self.start_time, self.end_time, self.reconciled_run_length
            )
        )


@dataclass
class LayerStructure:
    """Simulation vertical layer structure.

    This class defines the structure of the vertical dimension of the Virtual Ecosystem
    from a model configuration. Four values from the ``core.layers`` configuration
    section are used to define a set of vertical layers and their heights (or relative
    heights): ``canopy_layers``, ``soil_layers``, ``above_canopy_height_offset`` and
    ``surface_layer_height``. These values are validated and then assigned to attributes
    of this class. The ``n_layers`` and ``layer_roles`` attributes report the total
    number of layers in the vertical dimension and an array giving the vertical sequence
    of layer roles.

    The layer structure is shown below, along with values from the default
    configuration. All heights are in metres relative to ground level and the canopy
    layer heights are defined dynamically by the
    :class:`~virtual_ecosystem.models.plants.plants_model.PlantsModel`.

    .. csv-table::
        :header: "Index", "Role", "Description", "Set by", "Default"
        :widths: 5, 10, 30, 30, 10

        0, "above", "Above canopy conditions", "``above_ground_canopy_offset``", "+2 m"
        1, "canopy", "Height of first canopy layer",  "``PlantsModel``", "--"
        "...", "canopy", "Height of other canopy layers",  "``PlantsModel``", "--"
        10, "canopy", "Height of the last canopy layer ", "``PlantsModel``", "--"
        11, "surface", "Near surface conditions", ``surface_layer_height``, "0.1 m"
        12, "topsoil", "Top soil layer depth",  ``soil_layers``, "-0.25 m"
        13, "subsoil", "First subsoil layer depth",  ``soil_layers``, "-1.25 m"

    .. role:: python(code)
        :language: python

    The instance also provides the ``role_indices`` and ``role_indices_bool`` attributes
    that provide dictionaries of array indices for the locations of each of the four
    vertical layer roles. For example, given the example table above,
    :python:`layer_structure.role_indices["topsoil"]` would return
    :python:`np.array([12])` and :python:`layer_structure.role_indices_bool["topsoil"]`
    would return :python:`np.array([False, ..., False, True, False])`.

    In addition to the main list of roles shown above, a
    :class:`~virtual_ecosystem.core.core_components.LayerStructure` instance also
    provides indexing for two other sets of layers.

    1. Microbially active soil layers. These are the soil layers that fall even
       partially above the configured `max_depth_of_microbial_activity`. The
       `soil_layer_thickness` attribute provides the thickness of each soil layer -
       including both top- and sub-soil layers - and the `soil_layer_active_thickness`
       records the depth of biologically active soil within each layer. The two indexing
       structures above then contain additional indices for `active_soil` layers, where
       soil layer active thickness is greater than zero.

    2. All soil layers. These are simply additional entries in the indexing structure
       for `all_soil` for the combined `topsoil` and `subsoil` layers.

    3. Atmospheric (non-soil) layers. These are simply the layer indices from `above`
       down to and including `surface`.

    The instance also provides the
    :meth:`~virtual_ecosystem.core.core_components.LayerStructure.from_template` method,
    which returns a new empty DataArray with the standard vertical layer structure and
    grid cell dimensions used across the Virtual Ecosystem models.

    Raises:
        ConfigurationError: If the configuration elements are incorrect for defining
            the model timing.
    """

    canopy_layers: int = field(init=False)
    """The maximum number of canopy layers."""
    soil_layers: NDArray[np.float32] = field(init=False)
    """A list of the depths of soil layer boundaries."""
    soil_layer_thickness: NDArray[np.float32] = field(init=False)
    """A list of the thicknesses of soil layers."""
    above_canopy_height_offset: float = field(init=False)
    """The height above the canopy of the provided reference climate variables."""
    surface_layer_height: float = field(init=False)
    """The height above ground used to represent surface conditions."""
    n_layers: int = field(init=False)
    """The total number of vertical layers in the model."""
    layer_indices: NDArray[np.int_] = field(init=False)
    """The numeric indices of the vertical layers in the model."""
    layer_roles: NDArray[np.str_] = field(init=False)
    """An array of the roles of the vertical layers within the model from top to
    bottom."""
    role_indices_bool: dict[str, NDArray[np.bool_]] = field(init=False)
    """A dictionary providing boolean indices of each role within the vertical layer
    structure."""
    role_indices: dict[str, NDArray[np.int_]] = field(init=False)
    """A dictionary providing integer indices of each roles within the vertical layer
    structure."""
    config: InitVar[Config]
    """A validated model configuration."""
    n_cells: int
    """The number of grid cells in the simulation."""
    max_depth_of_microbial_activity: float
    """The maximum depth of microbial activity (m)."""

    def __post_init__(self, config: Config) -> None:
        """Populate the ``LayerStructure`` instance.

        This method populates the ``LayerStructure`` attributes from the provided
        :class:`~virtual_ecosystem.core.config.Config` instance.

        Args:
            config: A Config instance.
        """

        lyr_config = config["core"]["layers"]

        # Validate configuration
        self.canopy_layers = _validate_positive_integer(lyr_config["canopy_layers"])
        self.soil_layers = np.array(_validate_soil_layers(lyr_config["soil_layers"]))

        # Other heights should all be positive floats
        for attr, value in (
            ("above_canopy_height_offset", lyr_config["above_canopy_height_offset"]),
            ("surface_layer_height", lyr_config["surface_layer_height"]),
        ):
            setattr(self, attr, _validate_positive_finite_numeric(value, attr))

        # Get the layer role sequence
        self.layer_roles = np.array(
            ["above"]
            + ["canopy"] * int(self.canopy_layers)
            + ["surface"]
            + ["topsoil"]
            + ["subsoil"] * (len(self.soil_layers) - 1)
        )

        # Record the number of layers and layer indices
        self.n_layers = len(self.layer_roles)
        self.layer_indices = np.arange(0, self.n_layers)

        # Set up the various indices onto those roles
        self.role_indices_bool = {
            layer_role: self.layer_roles == layer_role
            for layer_role in ("above", "canopy", "surface", "topsoil", "subsoil")
        }
        self.role_indices = {
            ky: np.nonzero(vl)[0] for ky, vl in self.role_indices_bool.items()
        }

        # Add the `all_soil` and `atmospheric` indices
        self.role_indices["all_soil"] = np.concatenate(
            [self.role_indices["topsoil"], self.role_indices["subsoil"]]
        )
        self.role_indices_bool["all_soil"] = np.logical_or(
            self.role_indices_bool["topsoil"], self.role_indices_bool["subsoil"]
        )
        self.role_indices_bool["atmosphere"] = np.logical_not(
            self.role_indices_bool["all_soil"]
        )
        self.role_indices["atmosphere"] = np.where(
            self.role_indices_bool["atmosphere"]
        )[0]

        # Check that the maximum depth of the last layer is greater than the max depth
        # of microbial activity.
        if self.soil_layers[-1] > -self.max_depth_of_microbial_activity:
            to_raise = ConfigurationError(
                "Maximum depth of soil layers is less than the maximum depth "
                "of microbial activity"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Generate indices and layer information for the soil layers containing
        # significant microbial activity
        soil_layer_boundaries = np.array([0, *self.soil_layers])
        self.soil_layer_thickness = -np.diff(soil_layer_boundaries)
        self.soil_layer_active_thickness = np.clip(
            np.minimum(
                self.soil_layer_thickness,
                (soil_layer_boundaries + self.max_depth_of_microbial_activity)[:-1],
            ),
            a_min=0,
            a_max=np.inf,
        )

        self.role_indices["active_soil"] = self.role_indices["all_soil"][
            self.soil_layer_active_thickness > 0
        ]
        self.role_indices_bool["active_soil"] = np.array(
            [v in self.role_indices["active_soil"] for v in np.arange(self.n_layers)]
        )

        # Create a private template data array with the simulation structure. This
        # should not be accessed directly to avoid the chance of someone modifying the
        # actual template.
        self._array_template: DataArray = DataArray(
            np.full((self.n_layers, self.n_cells), np.nan),
            dims=("layers", "cell_id"),
            coords={
                "layers": self.layer_indices,
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": np.arange(self.n_cells),
            },
        )

        LOGGER.info("Layer structure built from model configuration")

    def from_template(self, array_name: str | None = None) -> DataArray:
        """Get a DataArray with the simulation vertical structure.

        This method returns two dimensional :class:`xarray.DataArray` with coordinates
        set to match the layer roles and number of grid cells for the current
        simulation. The array is filled with ``np.nan`` values and the array name is set
        if a name is provided.

        Args:
            array_name: An optional variable name to assign to the returned data array.
        """

        # Note that copy defaults to a deep copy, which is what is needed.
        template_copy = self._array_template.copy()
        if array_name:
            template_copy.name = array_name

        return template_copy


def _validate_positive_integer(value: float | int) -> int:
    """Validation function for positive integer values including integer floats."""

    # Note that float.is_integer() traps np.inf and np.nan, both of which are floats
    if (
        (not isinstance(value, float | int))
        or (isinstance(value, int) and value < 1)
        or (isinstance(value, float) and (not value.is_integer() or value < 1))
    ):
        to_raise = ConfigurationError(
            "The number of canopy layers is not a positive integer."
        )
        LOGGER.error(to_raise)
        raise to_raise

    return int(value)


def _validate_soil_layers(soil_layers: list[int | float]) -> list[int | float]:
    """Validation function for soil layer configuration setting."""

    # NOTE - this could become a validate_decreasing_negative_numerics() if we ever
    #        needed that more widely.

    if not isinstance(soil_layers, list) or len(soil_layers) < 1:
        to_raise = ConfigurationError(
            "The soil layers must be a non-empty list of layer depths."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if not all([isinstance(v, float | int) for v in soil_layers]):
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

    return soil_layers


def _validate_positive_finite_numeric(value: float | int, label: str) -> float | int:
    """Validation function for positive numeric values."""

    if (
        not isinstance(value, float | int)
        or np.isinf(value)
        or np.isnan(value)
        or value < 0
    ):
        to_raise = ConfigurationError(f"The {label} value must be a positive numeric.")
        LOGGER.error(to_raise)
        raise to_raise

    return value
