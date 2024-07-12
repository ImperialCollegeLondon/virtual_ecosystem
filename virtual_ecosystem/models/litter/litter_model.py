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
"""  # noqa: D205

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
from virtual_ecosystem.models.litter.input_partition import (
    calculate_litter_input_lignin_concentrations,
    partion_plant_inputs_between_pools,
)
from virtual_ecosystem.models.litter.litter_pools import (
    calculate_decay_rates,
    calculate_lignin_updates,
    calculate_total_C_mineralised,
    calculate_updated_pools,
)


class LitterModel(
    BaseModel,
    model_name="litter",
    model_update_bounds=("30 minutes", "3 months"),
    vars_required_for_init=(
        "litter_pool_above_metabolic",
        "litter_pool_above_structural",
        "litter_pool_woody",
        "litter_pool_below_metabolic",
        "litter_pool_below_structural",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
    ),
    vars_populated_by_init=(),
    vars_required_for_update=(
        "litter_pool_above_metabolic",
        "litter_pool_above_structural",
        "litter_pool_woody",
        "litter_pool_below_metabolic",
        "litter_pool_below_structural",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
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
    vars_populated_by_first_update=("litter_C_mineralisation_rate",),
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

        This function first calculates the decay rates for each litter pool, as well as
        the total carbon mineralisation rate. Once this is done, plant inputs to each
        pool are calculated, and used to find the new mass and lignin concentration of
        each litter pool.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # Calculate the litter pool decay rates
        decay_rates = calculate_decay_rates(
            above_metabolic=self.data["litter_pool_above_metabolic"].to_numpy(),
            above_structural=self.data["litter_pool_above_structural"].to_numpy(),
            woody=self.data["litter_pool_woody"].to_numpy(),
            below_metabolic=self.data["litter_pool_below_metabolic"].to_numpy(),
            below_structural=self.data["litter_pool_below_structural"].to_numpy(),
            lignin_above_structural=self.data["lignin_above_structural"].to_numpy(),
            lignin_woody=self.data["lignin_woody"].to_numpy(),
            lignin_below_structural=self.data["lignin_below_structural"].to_numpy(),
            surface_temp=self.data["air_temperature"][
                self.layer_structure.index_surface_scalar
            ].to_numpy(),
            topsoil_temp=self.data["soil_temperature"][
                self.layer_structure.index_topsoil_scalar
            ].to_numpy(),
            water_potential=self.data["matric_potential"][
                self.layer_structure.index_topsoil_scalar
            ].to_numpy(),
            constants=self.model_constants,
        )

        # Calculate the total mineralisation of carbon from the litter
        total_C_mineralisation_rate = calculate_total_C_mineralised(
            decay_rates,
            model_constants=self.model_constants,
            core_constants=self.core_constants,
        )

        # Find the plant inputs to each of the litter pools
        plant_inputs = partion_plant_inputs_between_pools(
            deadwood_production=self.data["deadwood_production"].to_numpy(),
            leaf_turnover=self.data["leaf_turnover"].to_numpy(),
            reproduct_turnover=self.data[
                "plant_reproductive_tissue_turnover"
            ].to_numpy(),
            root_turnover=self.data["root_turnover"].to_numpy(),
            leaf_turnover_lignin_proportion=self.data[
                "leaf_turnover_lignin"
            ].to_numpy(),
            reproduct_turnover_lignin_proportion=self.data[
                "plant_reproductive_tissue_turnover_lignin"
            ].to_numpy(),
            root_turnover_lignin_proportion=self.data[
                "root_turnover_lignin"
            ].to_numpy(),
            leaf_turnover_c_n_ratio=self.data["leaf_turnover_c_n_ratio"].to_numpy(),
            reproduct_turnover_c_n_ratio=self.data[
                "plant_reproductive_tissue_turnover_c_n_ratio"
            ].to_numpy(),
            root_turnover_c_n_ratio=self.data["root_turnover_c_n_ratio"].to_numpy(),
            constants=self.model_constants,
        )

        # Calculate the updated pool masses
        updated_pools = calculate_updated_pools(
            above_metabolic=self.data["litter_pool_above_metabolic"].to_numpy(),
            above_structural=self.data["litter_pool_above_structural"].to_numpy(),
            woody=self.data["litter_pool_woody"].to_numpy(),
            below_metabolic=self.data["litter_pool_below_metabolic"].to_numpy(),
            below_structural=self.data["litter_pool_below_structural"].to_numpy(),
            decomposed_excrement=self.data["decomposed_excrement"].to_numpy(),
            decomposed_carcasses=self.data["decomposed_carcasses"].to_numpy(),
            decay_rates=decay_rates,
            plant_inputs=plant_inputs,
            update_interval=self.model_timing.update_interval_quantity.to(
                "day"
            ).magnitude,
        )

        # Find lignin concentration of the litter input flows
        input_lignin = calculate_litter_input_lignin_concentrations(
            deadwood_lignin_proportion=self.data["deadwood_lignin"].to_numpy(),
            root_turnover_lignin_proportion=self.data[
                "root_turnover_lignin"
            ].to_numpy(),
            leaf_turnover_lignin_proportion=self.data[
                "leaf_turnover_lignin"
            ].to_numpy(),
            reproduct_turnover_lignin_proportion=self.data[
                "plant_reproductive_tissue_turnover_lignin"
            ].to_numpy(),
            root_turnover=self.data["root_turnover"].to_numpy(),
            leaf_turnover=self.data["leaf_turnover"].to_numpy(),
            reproduct_turnover=self.data[
                "plant_reproductive_tissue_turnover"
            ].to_numpy(),
            plant_input_above_struct=plant_inputs["above_ground_structural"],
            plant_input_below_struct=plant_inputs["below_ground_structural"],
        )

        # Find the changes in the lignin concentrations of the 3 relevant pools
        change_in_lignin = calculate_lignin_updates(
            lignin_above_structural=self.data["lignin_above_structural"].to_numpy(),
            lignin_woody=self.data["lignin_woody"].to_numpy(),
            lignin_below_structural=self.data["lignin_below_structural"].to_numpy(),
            plant_inputs=plant_inputs,
            input_lignin=input_lignin,
            updated_pools=updated_pools,
        )

        # Construct dictionary of data arrays to return
        updated_litter_variables = {
            "litter_pool_above_metabolic": DataArray(
                updated_pools["above_metabolic"], dims="cell_id"
            ),
            "litter_pool_above_structural": DataArray(
                updated_pools["above_structural"], dims="cell_id"
            ),
            "litter_pool_woody": DataArray(updated_pools["woody"], dims="cell_id"),
            "litter_pool_below_metabolic": DataArray(
                updated_pools["below_metabolic"], dims="cell_id"
            ),
            "litter_pool_below_structural": DataArray(
                updated_pools["below_structural"], dims="cell_id"
            ),
            "lignin_above_structural": DataArray(
                self.data["lignin_above_structural"]
                + change_in_lignin["above_structural"],
                dims="cell_id",
            ),
            "lignin_woody": DataArray(
                self.data["lignin_woody"] + change_in_lignin["woody"], dims="cell_id"
            ),
            "lignin_below_structural": DataArray(
                self.data["lignin_below_structural"]
                + change_in_lignin["below_structural"],
                dims="cell_id",
            ),
            "litter_C_mineralisation_rate": DataArray(
                total_C_mineralisation_rate, dims="cell_id"
            ),
        }

        # And then use then to update the litter variables
        self.data.add_from_dict(updated_litter_variables)

    def cleanup(self) -> None:
        """Placeholder function for litter model cleanup."""
