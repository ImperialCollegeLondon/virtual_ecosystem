"""The :mod:`~virtual_ecosystem.models.litter.litter_model` module creates a
:class:`~virtual_ecosystem.models.litter.litter_model.LitterModel` class as a child of
the :class:`~virtual_ecosystem.core.base_model.BaseModel` class. At present a lot of
the abstract methods of the parent class (e.g.
:func:`~virtual_ecosystem.core.base_model.BaseModel.setup` and
:func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Ecosystem
model develops. The factory method
:func:`~virtual_ecosystem.models.litter.litter_model.LitterModel.from_config` exists in
a more complete state, and unpacks a small number of parameters from our currently
pretty minimal configuration dictionary. These parameters are then used to generate a
class instance. If errors crop here when converting the information from the config
dictionary to the required types (e.g. :class:`~numpy.timedelta64`) they are caught and
then logged, and at the end of the unpacking an error is thrown. This error should be
caught and handled by downstream functions so that all model configuration failures can
be reported as one.
"""  # noqa: D205, D415

# TODO - At the moment this model only receives two things from the animal model,
# excrement and decayed carcass biomass. Both of these are simply added to the above
# ground metabolic litter. In future, bones and feathers should also be added, these
# will be handled using the more recalcitrant litter pools. However, we are leaving off
# adding these for now as they have minimal effects on the carbon cycle, though they
# probably matter for other nutrient cycles.

# FUTURE - Potentially make a more numerically accurate version of this model by using
# differential equations at some point. In reality, litter chemistry should change
# continuously with time not just at the final time step as in the current
# implementation. This is turn means that the decay rates should change continuously. I
# think the current implementation is fine, because this will be a small inaccuracy in a
# weakly coupled part of the model. However, if we ever become interested in precisely
# quantifying litter stocks then a differential version of this model should be created.

from __future__ import annotations

from typing import Any

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.litter.constants import LitterConsts
from virtual_ecosystem.models.litter.litter_pools import (
    calculate_change_in_litter_variables,
)


class LitterModel(
    BaseModel,
    model_name="litter",
    model_update_bounds=("30 minutes", "3 months"),
    required_init_vars=(
        ("litter_pool_above_metabolic", ("spatial",)),
        ("litter_pool_above_structural", ("spatial",)),
        ("litter_pool_woody", ("spatial",)),
        ("litter_pool_below_metabolic", ("spatial",)),
        ("litter_pool_below_structural", ("spatial",)),
        ("lignin_above_structural", ("spatial",)),
        ("lignin_woody", ("spatial",)),
        ("lignin_below_structural", ("spatial",)),
    ),
    vars_updated=(
        "litter_pool_above_metabolic",
        "litter_pool_above_structural",
        "litter_pool_woody",
        "litter_pool_below_metabolic",
        "litter_pool_below_structural",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
        "litter_C_mineralisation_rate",
    ),
):
    """A class defining the litter model.

    This model can be configured based on the data object and a config dictionary. At
    present the underlying model this class wraps is quite simple (i.e. two litter
    pools), but this will get more complex as the Virtual Ecosystem develops.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        model_constants: Set of constants for the litter model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: LitterConsts = LitterConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        # Check that no litter pool is negative
        all_pools = [
            "litter_pool_above_metabolic",
            "litter_pool_above_structural",
            "litter_pool_woody",
            "litter_pool_below_metabolic",
            "litter_pool_below_structural",
        ]
        negative_pools = []
        for pool in all_pools:
            if np.any(data[pool] < 0):
                negative_pools.append(pool)

        if negative_pools:
            to_raise = InitialisationError(
                f"Negative pool sizes found in: {', '.join(negative_pools)}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check that lignin proportions are between 0 and 1
        lignin_proportions = [
            "lignin_above_structural",
            "lignin_woody",
            "lignin_below_structural",
        ]
        bad_proportions = []
        for lignin_prop in lignin_proportions:
            if np.any(data[lignin_prop] < 0) or np.any(data[lignin_prop] > 1):
                bad_proportions.append(lignin_prop)

        if bad_proportions:
            to_raise = InitialisationError(
                "Lignin proportions not between 0 and 1 found in: "
                f"{', '.join(bad_proportions)}",
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.model_constants = model_constants
        """Set of constants for the litter model."""

        # Find first soil layer from the list of layer roles
        self.top_soil_layer_index: int = self.layer_structure.layer_roles.index("soil")
        """The layer in the data object representing the first soil layer."""
        # Find first soil layer from the list of layer roles
        self.surface_layer_index: int = self.layer_structure.layer_roles.index(
            "surface"
        )
        """The layer in the data object representing the surface layer."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> LitterModel:
        """Factory function to initialise the litter model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(config, "litter", "LitterConsts")

        LOGGER.info(
            "Information required to initialise the litter model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            model_constants=model_constants,
        )

    def setup(self) -> None:
        """Placeholder function to setup up the litter model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the litter model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Calculate changes in the litter pools and use them to update the pools.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        # Find change in litter variables using the function
        updated_variables = calculate_change_in_litter_variables(
            surface_temp=self.data["air_temperature_mean"][
                self.surface_layer_index
            ].to_numpy(),
            topsoil_temp=self.data["soil_temperature_mean"][
                self.top_soil_layer_index
            ].to_numpy(),
            water_potential=self.data["matric_potential_mean"][
                self.top_soil_layer_index
            ].to_numpy(),
            model_constants=self.model_constants,
            core_constants=self.core_constants,
            update_interval=self.model_timing.update_interval_quantity.to(
                "day"
            ).magnitude,
            above_metabolic=self.data["litter_pool_above_metabolic"].to_numpy(),
            above_structural=self.data["litter_pool_above_structural"].to_numpy(),
            woody=self.data["litter_pool_woody"].to_numpy(),
            below_metabolic=self.data["litter_pool_below_metabolic"].to_numpy(),
            below_structural=self.data["litter_pool_below_structural"].to_numpy(),
            lignin_above_structural=self.data["lignin_above_structural"].to_numpy(),
            lignin_woody=self.data["lignin_woody"].to_numpy(),
            lignin_below_structural=self.data["lignin_below_structural"].to_numpy(),
            decomposed_excrement=self.data["decomposed_excrement"].to_numpy(),
            decomposed_carcasses=self.data["decomposed_carcasses"].to_numpy(),
        )

        # Construct dictionary of data arrays
        updated_litter_variables = {
            variable: DataArray(updated_variables[variable], dims="cell_id")
            for variable in updated_variables.keys()
        }

        # And then use then to update the litter variables
        self.data.add_from_dict(updated_litter_variables)

    def cleanup(self) -> None:
        """Placeholder function for litter model cleanup."""
