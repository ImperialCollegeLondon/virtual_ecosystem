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
import pint
from numpy import datetime64, timedelta64
from scipy.integrate import solve_ivp
from xarray import DataArray, Dataset

from virtual_rainforest.core.base_model import BaseModel, InitialisationError
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates


class IntegrationError(Exception):
    """Custom exception class for cases when model integration cannot be completed."""


class SoilModel(BaseModel):
    """A class describing the soil model.

    Describes the specific functions and attributes that the soil module should possess.
    It's very much incomplete at the moment, and only overwrites one function in a
    pretty basic manner. This is intended as a demonstration of how the class
    inheritance should be handled for the model classes.

    Args:
        data: The data object to be used in the model.
        start_time: A datetime64 value setting the start time of the model.
        update_interval: Time to wait between updates of the model state.
        no_layers: The number of soil layers to be modelled.
    """

    model_name = "soil"
    """An internal name used to register the model and schema"""
    required_init_vars = (
        ("mineral_associated_om", ("spatial",)),
        ("low_molecular_weight_c", ("spatial",)),
        ("pH", ("spatial",)),
        ("bulk_density", ("spatial",)),
        ("soil_moisture", ("spatial",)),
        ("soil_temperature", ("spatial",)),
        ("percent_clay", ("spatial",)),
    )
    """Required initialisation variables for the soil model.

    This is a set of variables that must be present in the data object used to create a
    SoilModel , along with any core axes that those variables must map on
    to."""

    def __init__(
        self,
        data: Data,
        update_interval: timedelta64,
        start_time: datetime64,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, start_time, **kwargs)

        # Check that soil pool data is appropriately bounded
        if np.any(data["mineral_associated_om"] < 0.0) or np.any(
            data["low_molecular_weight_c"] < 0.0
        ):
            to_raise = InitialisationError(
                "Initial carbon pools contain at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.update_interval
        """The time interval between model updates."""
        self.next_update
        """The simulation time at which the model should next run the update method"""

    @classmethod
    def from_config(cls, data: Data, config: dict[str, Any]) -> SoilModel:
        """Factory function to initialise the soil model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.

        Raises:
            InitialisationError: If configuration data can't be properly converted
        """

        # Assume input is valid until we learn otherwise
        valid_input = True
        try:
            raw_interval = pint.Quantity(config["soil"]["model_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")
            start_time = datetime64(config["core"]["timing"]["start_time"])
        except (
            ValueError,
            pint.errors.DimensionalityError,
            pint.errors.UndefinedUnitError,
        ) as e:
            valid_input = False
            LOGGER.error(
                "Configuration types appear not to have been properly validated. This "
                "problem prevents initialisation of the soil model. The first instance"
                " of this problem is as follows: %s" % str(e)
            )

        if valid_input:
            LOGGER.info(
                "Information required to initialise the soil model successfully "
                "extracted."
            )
            return cls(data, update_interval, start_time)
        else:
            raise InitialisationError()

    def setup(self) -> None:
        """Placeholder function to setup up the soil model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def update(self) -> None:
        """Function to update the soil model."""

        # Convert DataArrays to numpy arrays
        low_molecular_weight_c = self.data["low_molecular_weight_c"].to_numpy()
        mineral_associated_om = self.data["mineral_associated_om"].to_numpy()

        # TODO - SWITCH TO USING INTEGRATE FUNCTION HERE
        carbon_pool_updates = calculate_soil_carbon_updates(
            low_molecular_weight_c,
            mineral_associated_om,
            self.data["pH"],
            self.data["bulk_density"],
            self.data["soil_moisture"],
            self.data["soil_temperature"],
            self.data["percent_clay"],
        )

        # Update carbon pools (attributes and data object)
        # n.b. this also updates the data object automatically
        self.replace_soil_pools(carbon_pool_updates)

        # Finally increment timing
        self.next_update += self.update_interval

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""

    def replace_soil_pools(self, new_pools: np.ndarray) -> None:
        """Replace soil pools with previously calculated new pool values.

        The state of particular soil pools will effect the rate of other processes in
        the soil module. These processes in turn can effect the exchange rates between
        the original soil pools. Thus, a separate update function is necessary so that
        the new values for all soil module components can be calculated on a single
        state, which is then updated (using this function) when all values have been
        calculated.

        Args:
            new_pools: Array of new pool values to insert into the data object
        """

        # Find total number of cells
        no_cells = self.data.grid.n_cells

        self.data["low_molecular_weight_c"] = DataArray(
            new_pools[:no_cells], dims="cell_id"
        )
        self.data["mineral_associated_om"] = DataArray(
            new_pools[no_cells:], dims="cell_id"
        )

    def integrate_soil_model(self) -> Dataset:
        """Function to integrate the soil model.

        For now a single integration will be used to advance the entire soil module.
        However, this might get split into several separate integrations in future (if
        that is feasible).

        This function unpacks the variables that are to be integrated into a single
        numpy array suitable for integration. This order of this numpy array is as
        follows: [low_molecular_weight_c, mineral_associated_om].

        Returns:
            A data array containing the new pool values (i.e. the values at the final
            time point)

        Raises:
            IntegrationError: When the integration cannot be successfully completed.
        """

        # Find number of grid cells integration is being performed over
        no_cells = self.data.grid.n_cells

        # Extract update interval
        update_time = self.update_interval.astype("timedelta64[s]").astype(float)
        # Convert from second to day units
        t_span = (0.0, update_time / (60.0 * 60.0 * 24.0))

        # Construct vector of initial values y0
        y0 = np.concatenate(
            [
                self.data["low_molecular_weight_c"].to_numpy(),
                self.data["mineral_associated_om"].to_numpy(),
            ]
        )

        # Carry out simulation
        output = solve_ivp(
            construct_full_soil_model,
            t_span,
            y0,
            args=(
                self.data,
                no_cells,
            ),
        )

        # Check whether or not integration succeeded
        if output.success:
            return Dataset(
                data_vars=dict(
                    new_lmwc=DataArray(output.y[:no_cells, -1], dims="cell_id"),
                    new_maom=DataArray(output.y[no_cells:, -1], dims="cell_id"),
                )
            )
        else:
            LOGGER.error(
                "Integration of soil module failed with following message: %s"
                % str(output.message)
            )
            raise IntegrationError()


def construct_full_soil_model(
    t: float, pools: np.ndarray, data: Data, no_cells: int
) -> np.ndarray:
    """Function that constructs the full soil model in a solve_ivp friendly form.

    Args:
        pools: And area containing all soil pools in a single vector
        data: The data object, used to populate the arguments i.e. pH and bulk density
        no_cells: Number of grid cells the integration is being performed over

    Returns:
        The rate of change for each soil pool
    """

    pool_rate_of_changes = calculate_soil_carbon_updates(
        pools[:no_cells],
        pools[no_cells:],
        data["pH"],
        data["bulk_density"],
        data["soil_moisture"],
        data["soil_temperature"],
        data["percent_clay"],
    )

    return pool_rate_of_changes
