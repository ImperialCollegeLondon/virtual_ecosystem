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


class LayerStructure:
    """Vertical layer structure of the Virtual Ecosystem.

    This class defines the structure of the vertical dimension of a simulation using the
    Virtual Ecosystem. The vertical dimension is divided into a series of layers,
    ordered from above the canopy to the bottom of the soil, that perform different
    roles in the simulation. The layers are defined using the following five
    configuration settings from the ``[core.layers]`` section.

    * ``above_canopy_height_offset``: the height above the canopy top of the first layer
      role ``above``, which is used as the measurement height of reference climate data.
    * ``canopy_layers``: a fixed number of layers with the ``canopy`` role. Not all of
      these necessarily contain canopy during a simulation as the canopy structure
      within these layers is dynamic.
    * ``surface_layer_heights``: the height above ground level of the ground surface
      atmospheric layer.
    * ``soil_layers``: this provides the depths of the soil horizons to be used in the
      simulation and so sets the number of soil layers and the horizon depth for each
      layer relative to the surface.
    * ``max_depth_of_microbial_activity``: the depth limit of significant microbial
      activity.

    The layer structure is shown below, along with the default configured height values
    in metres relative to ground level.

    .. csv-table::
        :header: "Index", "Role", "Description", "Set by", "Default"
        :widths: 5, 10, 30, 30, 10

        0, "above", "Above canopy conditions", "``above_ground_canopy_offset``", "+2 m"
        1, "canopy", "Height of first canopy layer",  "``PlantsModel``", "--"
        "...", "canopy", "Height of other canopy layers",  "``PlantsModel``", "--"
        10, "canopy", "Height of the last canopy layer ", "``PlantsModel``", "--"
        11, "surface", "Near surface conditions", ``surface_layer_height``, "0.1 m"
        12, "topsoil", "Top soil layer depth",  ``soil_layers``, "-0.25 m"
        13, "subsoil", "First subsoil layer depth",  ``soil_layers``, "-1.00 m"

    .. role:: python(code)
        :language: python

    .. py:current_module:: ~virtual_ecosystem.core.core_components

    **Additional Roles**:
        The following additional roles and attributes are also defined when the instance
        is created.

        1. The ``active_soil`` role indicates soil layers that fall even partially above
           the configured `max_depth_of_microbial_activity`. The `soil_layer_thickness`
           attribute provides the thickness of each soil layer - including both top- and
           sub-soil layers - and the `soil_layer_active_thickness` records the thickness
           of biologically active soil within each layer. Note that the ``soil_layers``
           provides the sequence of depths of soil horizons relative to the surface and
           these values provide the thickness of individual layers: the default
           ``soil_layers`` values of ``[-0.25, -1.00]`` give thickness values of
           ``[0.25, 0.75]``.

        2. The ``all_soil`` role is the combination of the ``topsoil`` and ``subsoil``
           layers.

        3. The ``atmosphere`` role is the combination of ``above``, ``canopy`` and
           ``surface`` layers.

        4. The ``filled_canopy`` role indicates canopy layers that contain any canopy
           across all of the grid cells. Canopy layers below these layers do not contain
           any canopy, and this is initialised to show no filled canopy layers. The
           ``lowest_canopy_filled`` attribute contains an array showing the lowest
           filled canopy layer in each grid cell. It contains ``np.nan`` when there is
           no canopy in a grid cell and is initalised as an array of ``np.nan`` values.

           Both of these are updated by the :meth:`~LayerStructure.set_filled_canopy`
           method, which is used to dynamically update these layer components during a
           simulation.

    **Layer indexing**:

        The class contains two private attributes (``_role_indices_bool`` and
        ``_role_indices_int``) that contain dictionaries of role indices as either
        boolean or integer indices. These dictionaries are keyed using frozensets of
        layer roles to allow both indicices for single roles and to add cache additional
        user requested aggregate role indices. User access to these dictionaries is
        through the :meth:`~LayerStructure.get_indices` method.

    **Methods overview**:

        * :meth:`~LayerStructure.get_indices`: this returns indices across the
          vertical layer dimension. As well as accepting single role names (e.g.
          ``get_indices('canopy')``), this method also constructs and caches aggregate
          indices (e.g. ``get_indices(['above','filled_canopy','surface'])``).

        * :meth:`~LayerStructure.from_template`: this returns an empty DataArray with
          the standard vertical layer structure and grid cell dimensions used across the
          Virtual Ecosystem models.

        * :meth:`~LayerStructure.set_filled_canopy`: this method is used to update the
          ``filled_canopy`` role indices and the ``lowest_canopy_filled` attribute,
          along with any cached aggregate indices using the ``filled_canopy`` role.

    Raises:
        ConfigurationError: If the configuration elements are incorrect for defining
            the layer structure.
    """

    def __init__(
        self, config: Config, n_cells: int, max_depth_of_microbial_activity: float
    ) -> None:
        """Populate the ``LayerStructure`` instance.

        This method populates the ``LayerStructure`` attributes from the provided
        :class:`~virtual_ecosystem.core.config.Config` instance.

        Args:
            config: A Config instance.
            n_cells: The number of grid cells in the simulation.
            max_depth_of_microbial_activity: The maximum depth of soil microbial
                activity (m).
        """

        lyr_config = config["core"]["layers"]

        # Validate configuration
        self.n_canopy_layers: int = _validate_positive_integer(
            lyr_config["canopy_layers"]
        )
        """The maximum number of canopy layers."""
        self.soil_layer_depth: NDArray[np.float_] = np.array(
            _validate_soil_layers(lyr_config["soil_layers"])
        )
        """A list of the depths of soil layer boundaries."""
        self.n_soil_layers: int = len(self.soil_layer_depth)
        """The number of soil layers."""
        # Other heights should all be positive floats
        self.above_canopy_height_offset: float = _validate_positive_finite_numeric(
            lyr_config["above_canopy_height_offset"], "above_canopy_height_offset"
        )
        """The height above the canopy of the provided reference climate variables."""
        self.surface_layer_height: float = _validate_positive_finite_numeric(
            lyr_config["surface_layer_height"], "surface_layer_height"
        )
        """The height above ground used to represent surface conditions."""

        # Store init arguments - these could be accessed directly from config, but
        # the core components flow then validates these values
        self._n_cells = n_cells
        """Number of grid cells in simulation."""
        self.max_depth_of_microbial_activity = max_depth_of_microbial_activity
        """The maximum soil depth of significant microbial activity."""

        # Check that the maximum depth of the last layer is greater than the max depth
        # of microbial activity.
        if self.soil_layer_depth[-1] > -self.max_depth_of_microbial_activity:
            to_raise = ConfigurationError(
                "Maximum depth of soil layers is less than the maximum depth "
                "of microbial activity"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Set the layer role sequence
        self.layer_roles: NDArray[np.str_] = np.array(
            ["above"]
            + ["canopy"] * self.n_canopy_layers
            + ["surface"]
            + ["topsoil"]
            + ["subsoil"] * (self.n_soil_layers - 1)
        )
        """An array of vertical layer role names from top to bottom."""

        # Record the number of layers and layer indices
        self.n_layers = len(self.layer_roles)
        """The total number of vertical layers in the model."""
        self.layer_indices = np.arange(0, self.n_layers)
        """An array of the integer indices of the vertical layers in the model."""

        # Document and type the role index attributes
        self._role_indices_bool: dict[str, NDArray[np.bool_]]
        """A dictionary providing boolean arrays indexing the location of sets of roles
         within the vertical layer structure."""
        self._role_indices_int: dict[str, NDArray[np.int_]]
        """A dictionary providing integer arrays indexing the location of sets of roles
         within the vertical layer structure."""

        self.lowest_canopy_filled = np.repeat(np.nan, self._n_cells)
        """An integer index showing the lowest filled canopy layer for each grid cell"""

        # Set up further soil layers details - layer thickness and the thickness of
        # microbially active soils within each layer
        soil_layer_boundaries = np.array([0, *self.soil_layer_depth])
        self.soil_layer_thickness = -np.diff(soil_layer_boundaries)
        """Thickness of each soil layer (m)"""
        self.soil_layer_active_thickness = np.clip(
            np.minimum(
                self.soil_layer_thickness,
                (soil_layer_boundaries + self.max_depth_of_microbial_activity)[:-1],
            ),
            a_min=0,
            a_max=np.inf,
        )
        """Thickness of microbially active soil in each soil layer (m)"""

        # Now define the initial indices and create the layer data template
        self._initialise_indices()

        # Create a private template data array with the simulation structure. This
        # should not be accessed directly to avoid the chance of someone modifying the
        # actual template.

        # PERFORMANCE - does deepcopy of a template provide any real benefit over
        # from_template creating it when called.
        self._array_template: DataArray = DataArray(
            np.full((self.n_layers, self._n_cells), np.nan),
            dims=("layers", "cell_id"),
            coords={
                "layers": self.layer_indices,
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": np.arange(self._n_cells),
            },
        )
        """A private data array template. Access copies using get_template."""

        LOGGER.info("Layer structure built from model configuration")

    def _initialise_indices(self):
        """Initialise the various layer indices.

        This method is called during instance initialisation to populate the role
        indices.
        """

        # The five core role names
        for layer_role in ("above", "canopy", "surface", "topsoil", "subsoil"):
            self._set_base_index(layer_role, self.layer_roles == layer_role)

        # Add the `all_soil` and `atmospheric` indices
        self._set_base_index(
            "all_soil",
            np.logical_or(
                self._role_indices_bool["topsoil"], self._role_indices_bool["subsoil"]
            ),
        )

        self._set_base_index("atmosphere", ~self._role_indices_bool["all_soil"])

        self._set_base_index(
            "active_soil",
            np.concatenate(
                [
                    np.repeat(False, self.n_canopy_layers + 2),
                    self.soil_layer_active_thickness > 0,
                ]
            ),
        )

        # Set the default filled canopy indices to an empty canopy
        self._set_base_index("filled_canopy", np.repeat(False, self.n_layers))

        # Set two additional widely used indices
        self._set_base_index(
            "filled_atmosphere",
            np.logical_or(
                self._role_indices_bool["above"],
                self._role_indices_bool["filled_canopy"],
                self._role_indices_bool["surface"],
            ),
        )

        self._set_base_index(
            "flux_layers",
            np.logical_or(
                self._role_indices_bool["filled_canopy"],
                self._role_indices_bool["topsoil"],
            ),
        )

    def _set_base_index(self, name: str, bool_values: NDArray[np.bool_]) -> None:
        """Helper method to populate the boolean and integer indices for base roles.

        Args:
            name: the name of the base role
            bool_values: the boolean representation of the index data.
        """
        self._role_indices_bool[name] = bool_values
        self._role_indices_int[name] = np.nonzero(bool_values)[0]

    def set_filled_canopy(self, canopy_heights: NDArray[np.float_]) -> None:
        """Set the dynamic canopy indices and attributes.

        The layer structure includes a fixed number of canopy layers but these layers
        are not all necessarily occupied. This method takes an array of canopy heights
        across the grid cells of the simulation and populates the "filled_canopy"
        indices, which are the canopy layers that contain at least one filled canopy
        layer. It also populates the "lowest_canopy_filled" attribute.

        Args:
            canopy_heights: A n_canopy_layers by n_grid_cells array of canopy layer
                heights.
        """

        if canopy_heights.shape != (self.n_canopy_layers, self._n_cells):
            to_raise = ValueError("canopy_heights array has wrong dimensions.")
            LOGGER.error(to_raise)
            raise to_raise

        # Update the filled canopy index
        canopy_present = ~np.isnan(canopy_heights)
        filled_canopy_bool = np.repeat(False, self.n_layers)
        filled_canopy_bool[1 : (self.n_canopy_layers + 1)] = np.any(
            canopy_present, axis=1
        )
        self._set_base_index("filled_canopy", filled_canopy_bool)

        # Set the lowest filled attribute
        lowest_filled = np.nansum(canopy_present, axis=0)
        self.lowest_canopy_filled = np.where(lowest_filled > 0, lowest_filled, np.nan)

        # Update indices that rely on filled canopy
        self._set_base_index(
            "filled_atmosphere",
            np.logical_or(
                self._role_indices_bool["above"],
                self._role_indices_bool["filled_canopy"],
                self._role_indices_bool["surface"],
            ),
        )

        self._set_base_index(
            "flux_layers",
            np.logical_or(
                self._role_indices_bool["filled_canopy"],
                self._role_indices_bool["topsoil"],
            ),
        )

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

    @property
    def index_above(self):
        """Layer indices for the above layer."""
        return self._role_indices_bool["above"]

    @property
    def index_canopy(self):
        """Layer indices for the above canopy layers."""
        return self._role_indices_bool["canopy"]

    @property
    def index_surface(self):
        """Layer indices for the surface layer."""
        return self._role_indices_bool["surface"]

    @property
    def index_topsoil(self):
        """Layer indices for the topsoil layer."""
        return self._role_indices_bool["topsoil"]

    @property
    def index_subsoil(self):
        """Layer indices for the subsoil layers."""
        return self._role_indices_bool["subsoil"]

    @property
    def index_all_soil(self):
        """Layer indices for all soil layers."""
        return self._role_indices_bool["all_soil"]

    @property
    def index_atmosphere(self):
        """Layer indices for all atmospheric layers."""
        return self._role_indices_bool["atmosphere"]

    @property
    def index_active_soil(self):
        """Layer indices for microbially active soil layers."""
        return self._role_indices_bool["active_soil"]

    @property
    def index_filled_canopy(self):
        """Layer indices for the filled canopy layers."""
        return self._role_indices_bool["filled_canopy"]

    @property
    def index_filled_atmosphere(self):
        """Layer indices for the filled atmospheric layers."""
        return self._role_indices_bool["filled_atmosphere"]

    @property
    def index_flux_layers(self):
        """Layer indices for the flux layers."""
        return self._role_indices_bool["flux_layers"]


def _validate_positive_integer(value: float | int) -> int:
    """Validation function for positive integer values including integer floats."""

    # Note that float.is_integer() traps np.infty and np.nan, both of which are floats
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
