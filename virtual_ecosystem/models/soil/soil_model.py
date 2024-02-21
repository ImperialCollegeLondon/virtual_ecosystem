"""The :mod:`~virtual_ecosystem.models.soil.soil_model` module creates a
:class:`~virtual_ecosystem.models.soil.soil_model.SoilModel` class as a child of the
:class:`~virtual_ecosystem.core.base_model.BaseModel` class. At present a lot of the
abstract methods of the parent class (e.g.
:func:`~virtual_ecosystem.core.base_model.BaseModel.setup` and
:func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Ecosystem
model develops. The factory method
:func:`~virtual_ecosystem.models.soil.soil_model.SoilModel.from_config` exists in a
more complete state, and unpacks a small number of parameters from our currently pretty
minimal configuration dictionary. These parameters are then used to generate a class
instance. If errors crop here when converting the information from the config dictionary
to the required types (e.g. :class:`~numpy.timedelta64`) they are caught and then
logged, and at the end of the unpacking an error is thrown. This error should be caught
and handled by downstream functions so that all model configuration failures can be
reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.soil.carbon import calculate_soil_carbon_updates
from virtual_ecosystem.models.soil.constants import SoilConsts


class IntegrationError(Exception):
    """Custom exception class for cases when model integration cannot be completed."""


class SoilModel(
    BaseModel,
    model_name="soil",
    model_update_bounds=("30 minutes", "3 months"),
    required_init_vars=(
        ("soil_c_pool_maom", ("spatial",)),
        ("soil_c_pool_lmwc", ("spatial",)),
        ("soil_c_pool_microbe", ("spatial",)),
        ("soil_c_pool_pom", ("spatial",)),
        ("pH", ("spatial",)),
        ("bulk_density", ("spatial",)),
        ("clay_fraction", ("spatial",)),
    ),
    vars_updated=(
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_microbe",
        "soil_c_pool_pom",
        "soil_enzyme_pom",
        "soil_enzyme_maom",
    ),
):
    """A class defining the soil model.

    This model can be configured based on the data object and a config dictionary. It
    can be updated by numerical integration. At present the underlying model this class
    wraps is quite simple (i.e. four soil carbon pools), but this will get more complex
    as the Virtual Ecosystem develops.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: A list giving the number and depth of soil layers to be modelled.
        canopy_layers: The number of canopy layers to be modelled.
        constants: Set of constants for the soil model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: SoilConsts,
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        # Check that soil pool data is appropriately bounded
        if (
            np.any(data["soil_c_pool_maom"] < 0.0)
            or np.any(data["soil_c_pool_lmwc"] < 0.0)
            or np.any(data["soil_c_pool_microbe"] < 0.0)
            or np.any(data["soil_c_pool_pom"] < 0.0)
        ):
            to_raise = InitialisationError(
                "Initial carbon pools contain at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Find first soil layer from the list of layer roles
        self.top_soil_layer_index = self.layer_structure.layer_roles.index("soil")
        """The layer in the data object representing the first soil layer."""

        # TODO - At the moment the soil model only cares about the very top layer. As
        # both the soil and abiotic models get more complex this might well change.
        self.model_constants = model_constants
        """Set of constants for the soil model."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> SoilModel:
        """Factory function to initialise the soil model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(config, "soil", "SoilConsts")

        LOGGER.info(
            "Information required to initialise the soil model successfully "
            "extracted."
        )

        return cls(
            data=data,
            core_components=core_components,
            model_constants=model_constants,
        )

    def setup(self) -> None:
        """Placeholder function to setup up the soil model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Update the soil model by integrating.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        # Find carbon pool updates by integration
        updated_carbon_pools = self.integrate()

        # Update carbon pools (attributes and data object)
        # n.b. this also updates the data object automatically
        self.data.add_from_dict(updated_carbon_pools)

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""

    def integrate(self) -> dict[str, DataArray]:
        """Integrate the soil model.

        For now a single integration will be used to advance the entire soil module.
        However, this might get split into several separate integrations in future (if
        that is feasible).

        This function unpacks the variables that are to be integrated into a single
        numpy array suitable for integration.

        Returns:
            A data array containing the new pool values (i.e. the values at the final
            time point)

        Raises:
            IntegrationError: When the integration cannot be successfully completed.
        """

        # Find number of grid cells integration is being performed over
        no_cells = self.data.grid.n_cells

        # Extract update interval (in units of number of days)
        update_time = self.model_timing.update_interval_quantity.to("days").magnitude
        t_span = (0.0, update_time)

        # Construct vector of initial values y0
        y0 = np.concatenate(
            [
                self.data[name].to_numpy()
                for name in map(str, self.data.data.keys())
                if name.startswith("soil_c_pool_") or name.startswith("soil_enzyme_")
            ]
        )

        # Find and store order of pools
        delta_pools_ordered = {
            name: np.array([])
            for name in map(str, self.data.data.keys())
            if name.startswith("soil_c_pool_") or name.startswith("soil_enzyme_")
        }

        # Carry out simulation
        output = solve_ivp(
            construct_full_soil_model,
            t_span,
            y0,
            args=(
                self.data,
                no_cells,
                self.top_soil_layer_index,
                delta_pools_ordered,
                self.model_constants,
                self.core_constants,
            ),
        )

        # Check if integration failed
        if not output.success:
            LOGGER.error(
                "Integration of soil module failed with following message: %s"
                % str(output.message)
            )
            raise IntegrationError()

        # Construct index slices
        slices = make_slices(no_cells, round(len(y0) / no_cells))

        # Construct dictionary of data arrays
        new_c_pools = {
            str(pool): DataArray(output.y[slc, -1], dims="cell_id")
            for slc, pool in zip(slices, delta_pools_ordered.keys())
        }

        return new_c_pools


def construct_full_soil_model(
    t: float,
    pools: NDArray[np.float32],
    data: Data,
    no_cells: int,
    top_soil_layer_index: int,
    delta_pools_ordered: dict[str, NDArray[np.float32]],
    model_constants: SoilConsts,
    core_constants: CoreConsts,
) -> NDArray[np.float32]:
    """Function that constructs the full soil model in a solve_ivp friendly form.

    Args:
        t: Current time [days]. At present the model has no explicit time dependence,
            but the function must still be accept a time value to allow it to be
            integrated.
        pools: An array containing all soil pools in a single vector
        data: The data object, used to populate the arguments i.e. pH and bulk density
        no_cells: Number of grid cells the integration is being performed over
        top_soil_layer_index: Index for layer in data object representing top soil layer
        delta_pools_ordered: Dictionary to store pool changes in the order that pools
            are stored in the initial condition vector.
        model_constants: Set of constants for the soil model.
        core_constants: Set of constants shared between models.

    Returns:
        The rate of change for each soil pool
    """

    # Construct index slices
    slices = make_slices(no_cells, len(delta_pools_ordered))

    # Construct dictionary of numpy arrays (using a for loop)
    soil_pools = {
        str(pool): pools[slc] for slc, pool in zip(slices, delta_pools_ordered.keys())
    }

    # Supply soil pools by unpacking dictionary
    return calculate_soil_carbon_updates(
        pH=data["pH"].to_numpy(),
        bulk_density=data["bulk_density"].to_numpy(),
        soil_moisture=data["soil_moisture"][top_soil_layer_index].to_numpy(),
        soil_water_potential=data["matric_potential"][top_soil_layer_index].to_numpy(),
        vertical_flow_rate=data["vertical_flow"].to_numpy(),
        soil_temp=data["soil_temperature"][top_soil_layer_index].to_numpy(),
        clay_fraction=data["clay_fraction"].to_numpy(),
        mineralisation_rate=data["litter_C_mineralisation_rate"].to_numpy(),
        delta_pools_ordered=delta_pools_ordered,
        model_constants=model_constants,
        core_constants=core_constants,
        **soil_pools,
    )


def make_slices(no_cells: int, no_pools: int) -> list[slice]:
    """Constructs a list of slices based on the number of grid cells and pools.

    Args:
        no_cells: Number of grid cells the pools are defined for
        no_pools: Number of soil pools being integrated

    Returns:
        A list of containing the correct number of correctly spaced slices
    """

    # Construct index slices
    return [slice(n * no_cells, (n + 1) * no_cells) for n in range(no_pools)]
