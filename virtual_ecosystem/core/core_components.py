"""This submodule contains a dataclass used to generate core common components required
by models. It is used as input to the
:class:`~virtual_ecosystem.core.base_model.BaseModel`, allowing single instances of
these components to be cascaded down to individual model subclass instances via the
``__init__`` method of the base model..
"""  # noqa: D205

from __future__ import annotations

from dataclasses import InitVar, dataclass, field

import numpy as np
import pint
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import (
    CoreConfiguration,
    CoreConstants,
    LayersConfiguration,
    TimingConfiguration,
)


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
    core_constants: CoreConstants = field(init=False)
    """The core constant definitions for the simulation."""
    config: InitVar[CoreConfiguration]
    """A validated model configuration."""

    def __post_init__(self, config: CoreConfiguration) -> None:
        """Populate the core components from the config."""
        self.grid = Grid.from_config(config=config.grid)
        self.core_constants = config.constants
        self.layer_structure = LayerStructure(
            config=config.layers,
            n_cells=self.grid.n_cells,
            max_depth_of_microbial_activity=self.core_constants.max_depth_of_microbial_activity,
        )
        self.model_timing = ModelTiming(config=config.timing)


@dataclass
class ModelTiming:
    """Model timing details.

    This data class defines the timing of a Virtual Ecosystem simulation from the
    {class}`~virtual_ecosystem.core.model_config.TimingConfiguration` section of a
    validated model configuration.

    The end time is calculated from the previously extracted timing information. This
    end time will always be the largest whole multiple of the update interval that
    exceeds or equal the configured ``run_length``.
    """

    start_time: np.datetime64 = field(init=False)
    """The start time of the simulation."""
    end_time: np.datetime64 = field(init=False)
    """The calculated end time of the simulation."""
    reconciled_run_length: np.timedelta64 = field(init=False)
    """The difference between start and calculated end time."""
    run_length: np.timedelta64 = field(init=False)
    """The configured run length."""
    update_interval: np.timedelta64 = field(init=False)
    """The configured update interval."""
    run_length_quantity: pint.Quantity = field(init=False)
    """The configured run length."""
    update_interval_quantity: pint.Quantity = field(init=False)
    """The configured update interval."""
    update_interval_seconds: float = field(init=False)
    """The configured update interval in seconds."""
    n_updates: int = field(init=False)
    """The total number of model updates in the configured run."""
    updates_per_year: np.float64 = field(init=False)
    """The number of updates per year based on update_interval."""
    config: InitVar[TimingConfiguration]
    """A validated model configuration."""

    def __post_init__(self, config: TimingConfiguration) -> None:
        """Populate the ``ModelTiming`` instance.

        This method populates the ``ModelTiming`` attributes from the provided
        :class:`~virtual_ecosystem.core.model_config.TimingConfiguration` instance.

        Args:
            config: A TimingConfiguration instance.
        """

        # Convert configuration into datetime64 and timedelta64
        self.start_time = np.datetime64(config.start_date)
        self.update_interval = np.timedelta64(int(config.update_interval_seconds), "s")
        self.run_length = np.timedelta64(int(config.run_length_seconds), "s")
        self.update_interval_quantity = pint.Quantity(config.update_interval)
        self.run_length_quantity = pint.Quantity(config.run_length)

        # Calculate when the simulation should stop as the first number of update
        # intervals to exceed the requested run length and calculate the actual run
        # length
        self.end_time = (
            self.start_time
            + np.ceil(self.run_length / self.update_interval) * self.update_interval
        )
        self.reconciled_run_length = self.end_time - self.start_time

        self.n_updates = int((self.end_time - self.start_time) / self.update_interval)

        # Calculate the number of updates in one year
        # TODO - this is not calendar aware - variable length months and leap years.
        seconds_per_year = np.timedelta64(31536000, "s")
        self.updates_per_year = seconds_per_year / self.update_interval

        # Calculate the total number of seconds in the update interval
        self.update_interval_seconds = float(
            self.update_interval / np.timedelta64(1, "s")
        )

        # Log the completed timing creation.
        LOGGER.info(
            "Timing details built from model configuration: "  # noqa: UP032
            "start - {}, end - {}, run length - {}".format(
                self.start_time, self.end_time, self.reconciled_run_length
            )
        )


@dataclass
class LayerStructure:
    """Vertical layer structure of the Virtual Ecosystem.

    This class defines the structure of the vertical dimension of a simulation using the
    Virtual Ecosystem. The vertical dimension is divided into a series of layers,
    ordered from above the canopy to the bottom of the soil, that perform different
    roles in the simulation. The configuration of the layer structure is defined in the
    :class:`virtual_ecosystem.core.model_config.LayersConfiguration` class.

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

    **Additional Roles**:
        The following additional roles and attributes are also defined when the instance
        is created and are constant through the runtime of the model.

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

    **Dynamic roles**:

        The following roles are set when the instance is initialised but are can be
        updated during the model run using the :meth:`.set_filled_canopy`
        method.

        1. The ``filled_canopy`` role indicates canopy layers that contain any canopy
           across all of the grid cells. No grid cell contains actual canopy in any of
           the canopy layers below the filled canopy layers. This is initialised to show
           no filled canopy layers.

        2, The ``filled_atmosphere`` role includes the above canopy layer, all filled
        canopy layer indices and the surface layer.

        3. The ``flux_layers`` role includes the filled canopy layers and the topsoil
           layer.

        In addition, the :attr:`.lowest_canopy_filled` attribute provides an array
        giving the vertical index of the lowest filled canopy layer in each grid cell.
        It contains ``np.nan`` when there is  no canopy in a grid cell and is
        initialised as an array of ``np.nan`` values.

    **Getting layer indices**:

        The :attr:`._role_indices_bool` and :attr:`._role_indices_int` attributes
        contain dictionaries keyed by role name of the boolean or integer indices of the
        different defined roles. However, all of the role indices should be accessed
        using the specific instance properties e.g. :attr:`.index_above`.

        Note that the standard index properties like :attr:`.index_above` will return an
        array index, which extracts a two dimensional slice of the vertical structure.
        It is sometimes more convenient to extract a 1 dimensional slice across cells,
        dropping the vertical dimension. This only makes sense for the role layers  that
        are by definition a single layer thick (``above``, ``surface`` and ``topsoil``),
        and for these three layers, additional properties (e.g.
        :attr:`.index_above_scalar`) are defined that will return a scalar index that
        extracts a one-dimensional slice.

    **Methods overview**:

        * :meth:`.from_template`: this returns an empty DataArray with
          the standard vertical layer structure and grid cell dimensions used across the
          Virtual Ecosystem models.

        * :meth:`.set_filled_canopy`: this method is used to update the
          ``filled_canopy`` role indices, the related ``filled_atmosphere`` and
          ``flux_layers`` roles, and the :attr:`.lowest_canopy_filled` attribute.

    Raises:
        ConfigurationError: If the configuration elements are incorrect for defining
            the layer structure.
    """

    config: InitVar[LayersConfiguration]
    """A configuration object instance."""

    # These two init arguments could also be accessed directly from the config, but
    # this allows for the core components flow from Grid and CoreConstants to validate
    # these values rather than doing it internally.
    n_cells: InitVar[int]
    """The number of grid cells in the simulation."""
    max_depth_of_microbial_activity: float
    """The maximum soil depth of significant microbial activity."""

    # Attributes populated by __post_init__
    n_canopy_layers: int = field(init=False)
    """The maximum number of canopy layers."""
    soil_layer_depths: NDArray[np.floating] = field(init=False)
    """A list of the depths of soil layer boundaries."""
    n_soil_layers: int = field(init=False)
    """The number of soil layers."""
    above_canopy_height_offset: float = field(init=False)
    """The height above the canopy of the provided reference climate variables."""
    surface_layer_height: float = field(init=False)
    """The height above ground used to represent surface conditions."""
    _n_cells: int = field(init=False)
    """Private record of the number of grid cells in simulation."""
    layer_roles: NDArray[np.str_] = field(init=False)
    """An array of vertical layer role names from top to bottom."""
    n_layers: int = field(init=False)
    """The total number of vertical layers in the model."""
    layer_indices: NDArray[np.int_] = field(init=False)
    """An array of the integer indices of the vertical layers in the model."""
    _role_indices_bool: dict[str, NDArray[np.bool_]] = field(
        init=False, default_factory=lambda: {}
    )
    """A dictionary of boolean layer role indices within the vertical structure."""
    _role_indices_int: dict[str, NDArray[np.int_]] = field(
        init=False, default_factory=lambda: {}
    )
    """A dictionary of integer layer role indices within the vertical structure."""
    _role_indices_scalar: dict[str, int] = field(init=False, default_factory=lambda: {})
    """A dictionary of scalar role indices within the vertical structure for single
    layer roles."""
    lowest_canopy_filled: NDArray[np.int_] = field(init=False)
    """An integer index showing the lowest filled canopy layer for each grid cell"""
    n_canopy_layers_filled: int = field(init=False)
    """The current number of filled canopy layers across grid cells"""
    soil_layer_thickness: NDArray[np.floating] = field(init=False)
    """Thickness of each soil layer (m)"""
    soil_layer_active_thickness: NDArray[np.floating] = field(init=False)
    """Thickness of the microbially active soil in each soil layer (m)"""
    _array_template: DataArray = field(init=False)
    """A private data array template. Access copies using get_template."""

    def __post_init__(self, config: LayersConfiguration, n_cells: int) -> None:
        """Populate the ``LayerStructure`` instance.

        This method populates the ``LayerStructure`` attributes from the dataclass init
        arguments.

        Args:
            config: A Config instance.
            n_cells: The number of grid cells in the simulation.
        """

        # Store the number of grid cells privately
        self._n_cells = n_cells

        # Validates the configuration inputs and sets the layer structure attributes
        self._initialise_layers(config)

        # Now populate the initial role indices and create the layer data template
        self._populate_role_indices()

        # Set the layer structure DataArray template
        self._set_layer_data_array_template()

        LOGGER.info("Layer structure built from model configuration")

    def _initialise_layers(self, config: LayersConfiguration):
        """Layer structure attribute initialisation.

        Args:
            config: A Config instance.
        """

        # Extract validated configuration values
        self.n_canopy_layers = config.canopy_layers
        self.soil_layer_depths = np.array(config.soil_layers)
        self.n_soil_layers = self.soil_layer_depths.size
        self.above_canopy_height_offset = config.above_canopy_height_offset
        self.surface_layer_height = config.surface_layer_height

        # Set the layer role sequence
        self.layer_roles: NDArray[np.str_] = np.array(
            ["above"]
            + ["canopy"] * self.n_canopy_layers
            + ["surface"]
            + ["topsoil"]
            + ["subsoil"] * (self.n_soil_layers - 1)
        )

        # Record the number of layers and layer indices
        self.n_layers = len(self.layer_roles)
        self.layer_indices = np.arange(0, self.n_layers)

        # Default values for lowest canopy filled and n filled canopy
        self.lowest_canopy_filled = np.repeat(np.nan, self._n_cells)
        self.n_canopy_layers_filled = 0

        # Check that the maximum depth of the last layer is greater than the max depth
        # of microbial activity.
        if self.soil_layer_depths[-1] > -self.max_depth_of_microbial_activity:
            to_raise = ConfigurationError(
                "Maximum depth of soil layers is less than the maximum depth "
                "of microbial activity"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Set up soil layer thickness and the thickness of microbially active soil
        soil_layer_boundaries = np.array([0, *self.soil_layer_depths])
        self.soil_layer_thickness = -np.diff(soil_layer_boundaries)
        self.soil_layer_active_thickness = np.clip(
            np.minimum(
                self.soil_layer_thickness,
                (soil_layer_boundaries + self.max_depth_of_microbial_activity)[:-1],
            ),
            a_min=0,
            a_max=np.inf,
        )

    def _populate_role_indices(self):
        """Populate the initial values for the layer role indices."""

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
            np.logical_or.reduce(
                (
                    self._role_indices_bool["above"],
                    self._role_indices_bool["filled_canopy"],
                    self._role_indices_bool["surface"],
                )
            ),
        )

        self._set_base_index(
            "flux_layers",
            np.logical_or(
                self._role_indices_bool["filled_canopy"],
                self._role_indices_bool["topsoil"],
            ),
        )

        # Set the scalar indices - using item here as a deliberate trap for accidental
        # definition of these layers as being more than a single layer.
        self._role_indices_scalar["above"] = self._role_indices_int["above"].item()
        self._role_indices_scalar["surface"] = self._role_indices_int["surface"].item()
        self._role_indices_scalar["topsoil"] = self._role_indices_int["topsoil"].item()

    def _set_layer_data_array_template(self):
        """Sets the template data array with the simulation vertical structure.

        This data array structure is widely used across the Virtual Ecosystem and this
        method sets up a template that can be copied via the
        :meth:`LayerStructure.from_template`
        method. The private attribute itself should not be accessed directly to avoid
        accidental  modification of the template.
        """

        # PERFORMANCE - does deepcopy of a store template provide any real benefit over
        # from_template creating it when called.

        self._array_template = DataArray(
            np.full((self.n_layers, self._n_cells), np.nan),
            dims=("layers", "cell_id"),
            coords={
                "layers": self.layer_indices,
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": np.arange(self._n_cells),
            },
        )

    def _set_base_index(self, name: str, bool_values: NDArray[np.bool_]) -> None:
        """Helper method to populate the boolean and integer indices for base roles.

        Args:
            name: the name of the base role
            bool_values: the boolean representation of the index data.
        """
        self._role_indices_bool[name] = bool_values
        self._role_indices_int[name] = np.nonzero(bool_values)[0]

    def set_filled_canopy(self, canopy_heights: NDArray[np.floating]) -> None:
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

        # Set the lowest filled attribute and number of layers
        lowest_filled = np.nansum(canopy_present, axis=0)
        self.lowest_canopy_filled = np.where(lowest_filled > 0, lowest_filled, np.nan)
        self.n_canopy_layers_filled = np.sum(filled_canopy_bool)

        # Update indices that rely on filled canopy
        self._set_base_index(
            "filled_atmosphere",
            np.logical_or.reduce(
                (
                    self._role_indices_bool["above"],
                    self._role_indices_bool["filled_canopy"],
                    self._role_indices_bool["surface"],
                )
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
    def index_above(self) -> NDArray[np.bool_]:
        """Layer indices for the above layer."""
        return self._role_indices_bool["above"]

    @property
    def index_canopy(self) -> NDArray[np.bool_]:
        """Layer indices for the above canopy layers."""
        return self._role_indices_bool["canopy"]

    @property
    def index_surface(self) -> NDArray[np.bool_]:
        """Layer indices for the surface layer."""
        return self._role_indices_bool["surface"]

    @property
    def index_topsoil(self) -> NDArray[np.bool_]:
        """Layer indices for the topsoil layer."""
        return self._role_indices_bool["topsoil"]

    @property
    def index_subsoil(self) -> NDArray[np.bool_]:
        """Layer indices for the subsoil layers."""
        return self._role_indices_bool["subsoil"]

    @property
    def index_all_soil(self) -> NDArray[np.bool_]:
        """Layer indices for all soil layers."""
        return self._role_indices_bool["all_soil"]

    @property
    def index_atmosphere(self) -> NDArray[np.bool_]:
        """Layer indices for all atmospheric layers."""
        return self._role_indices_bool["atmosphere"]

    @property
    def index_active_soil(self) -> NDArray[np.bool_]:
        """Layer indices for microbially active soil layers."""
        return self._role_indices_bool["active_soil"]

    @property
    def index_filled_canopy(self) -> NDArray[np.bool_]:
        """Layer indices for the filled canopy layers."""
        return self._role_indices_bool["filled_canopy"]

    @property
    def index_filled_atmosphere(self) -> NDArray[np.bool_]:
        """Layer indices for the filled atmospheric layers."""
        return self._role_indices_bool["filled_atmosphere"]

    @property
    def index_flux_layers(self) -> NDArray[np.bool_]:
        """Layer indices for the flux layers."""
        return self._role_indices_bool["flux_layers"]

    @property
    def index_above_scalar(self) -> int:
        """Layer indices for the above canopy layer."""
        return self._role_indices_scalar["above"]

    @property
    def index_topsoil_scalar(self) -> int:
        """Layer indices for the topsoil layer."""
        return self._role_indices_scalar["topsoil"]

    @property
    def index_surface_scalar(self) -> int:
        """Layer indices for the surface layer."""
        return self._role_indices_scalar["surface"]
