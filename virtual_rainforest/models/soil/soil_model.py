"""The :mod:`~virtual_rainforest.models.soil.soil_model` module creates a
:class:`~virtual_rainforest.models.soil.soil_model.SoilModel` class as a child of the
:class:`~virtual_rainforest.core.base_model.BaseModel` class. At present a lot of the
abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.setup` and
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.soil.soil_model.SoilModel.from_config` exists in a
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
from pint import Quantity
from scipy.integrate import solve_ivp
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.constants import load_constants
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates
from virtual_rainforest.models.soil.constants import SoilConsts


class IntegrationError(Exception):
    """Custom exception class for cases when model integration cannot be completed."""


class SoilModel(BaseModel):
    """A class defining the soil model.

    This model can be configured based on the data object and a config dictionary. It
    can be updated by numerical integration. At present the underlying model this class
    wraps is quite simple (i.e. four soil carbon pools), but this will get more complex
    as the Virtual Rainforest develops.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: A list giving the number and depth of soil layers to be modelled.
        canopy_layers: The number of canopy layers to be modelled.
        constants: Set of constants for the soil model.
    """

    model_name = "soil"
    """An internal name used to register the model and schema"""
    lower_bound_on_time_scale = "30 minutes"
    """Shortest time scale that soil model can sensibly capture."""
    upper_bound_on_time_scale = "3 months"
    """Longest time scale that soil model can sensibly capture."""
    required_init_vars = (
        ("soil_c_pool_maom", ("spatial",)),
        ("soil_c_pool_lmwc", ("spatial",)),
        ("soil_c_pool_microbe", ("spatial",)),
        ("soil_c_pool_pom", ("spatial",)),
        ("pH", ("spatial",)),
        ("bulk_density", ("spatial",)),
        ("percent_clay", ("spatial",)),
    )
    """Required initialisation variables for the soil model.

    This is a set of variables that must be present in the data object used to create a
    SoilModel , along with any core axes that those variables must map on
    to."""
    vars_updated = (
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_microbe",
        "soil_c_pool_pom",
    )
    """Variables updated by the soil model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: list[float],
        canopy_layers: int,
        constants: SoilConsts,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

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

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)
        # Find first soil layer from the list of layer roles
        self.top_soil_layer_index = next(
            i for i, v in enumerate(layer_roles) if v == "soil"
        )
        """The layer in the data object representing the first soil layer."""
        # TODO - At the moment the soil model only cares about the very top layer. As
        # both the soil and abiotic models get more complex this might well change.
        self.constants = constants
        """Set of constants for the soil model"""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> SoilModel:
        """Factory function to initialise the soil model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]

        # Load in the relevant constants
        constants = load_constants(config, "soil", "SoilConsts")

        LOGGER.info(
            "Information required to initialise the soil model successfully "
            "extracted."
        )
        return cls(data, update_interval, soil_layers, canopy_layers, constants)

    def setup(self) -> None:
        """Placeholder function to setup up the soil model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def update(self, time_index: int) -> None:
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
        update_time = self.update_interval.to("days").magnitude
        t_span = (0.0, update_time)

        # Construct vector of initial values y0
        y0 = np.concatenate(
            [
                self.data[str(name)].to_numpy()
                for name in self.data.data.keys()
                if str(name).startswith("soil_c_pool_")
            ]
        )

        # Find and store order of pools
        delta_pools_ordered = {
            str(name): np.array([])
            for name in self.data.data.keys()
            if str(name).startswith("soil_c_pool_")
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
                self.constants,
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
    constants: SoilConsts,
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
        constants: Set of constants for the soil model.

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
        soil_temp=data["soil_temperature"][top_soil_layer_index].to_numpy(),
        percent_clay=data["percent_clay"].to_numpy(),
        mineralisation_rate=data["litter_C_mineralisation_rate"].to_numpy(),
        delta_pools_ordered=delta_pools_ordered,
        constants=constants,
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
