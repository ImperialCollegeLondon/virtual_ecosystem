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
from xarray import Dataset

from virtual_rainforest.core.base_model import BaseModel, InitialisationError
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates


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

        # Convert time step from seconds to days
        dt = self.update_interval.astype("timedelta64[s]").astype(float) / (
            60.0 * 60.0 * 24.0
        )

        carbon_pool_updates = calculate_soil_carbon_updates(
            self.data,
            self.data["pH"],
            self.data["bulk_density"],
            self.data["soil_moisture"],
            self.data["soil_temperature"],
            self.data["percent_clay"],
        )

        # Update carbon pools (attributes and data object)
        # n.b. this also updates the data object automatically
        self.increment_soil_pools(carbon_pool_updates, dt)

        # Finally increment timing
        self.next_update += self.update_interval

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""

    def increment_soil_pools(self, delta_pools: Dataset, dt: float) -> None:
        """Increment soil pools based on previously calculated net change.

        The state of particular soil pools will effect the rate of other processes in
        the soil module. These processes in turn can effect the exchange rates between
        the original soil pools. Thus, a separate update function is necessary so that
        update increments for all soil module components can be calculated on a single
        state, which is then updated (using this function) when all increments have been
        calculated.

        Args:
            data: The data object to be used in the model.
            delta_pools: Array of updates for every pool
            dt: time step (days)
        """

        self.data["mineral_associated_om"] += delta_pools["delta_maom"] * dt
        self.data["low_molecular_weight_c"] += delta_pools["delta_lmwc"] * dt

    # TODO - Add appropriate testing for this
    def integrate_soil_model(self) -> Dataset:
        """Function to integrate the soil model.

        For now a single integration will be used to advance the entire soil module.
        However, this might get split into several separate integrations in future (if
        that is feasible).
        """

        # Extract update interval
        update_time = self.update_interval.astype("timedelta64[s]").astype(float)
        # Convert from second to day units
        t_span = (0.0, update_time / (60.0 * 60.0 * 24.0))

        # TODO - Construct vector of initial values y0
        y0: list[float] = []

        # TODO - Add actual integration here
        solve_ivp(construct_full_soil_model, t_span, y0)

        return Dataset()


# TODO - Work out how to test this function
# This takes and returns an array of numpy values
# Also a load of arguments, e.g. constants, pH, etc, etc
def construct_full_soil_model() -> None:
    """Function that constructs the full soil model in a solve_ivp friendly form."""
    # TODO - UNPACK DATA, IS THERE A WAY TO ESTABLISH VECTOR LENGTH?

    # TODO - RUN HIGHEST LEVEL FUNCTION
    # e.g. calculate_soil_carbon_updates()
