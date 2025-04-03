"""The :mod:`~virtual_ecosystem.models.litter.litter_model` module creates a
:class:`~virtual_ecosystem.models.litter.litter_model.LitterModel` class as a child of
the :class:`~virtual_ecosystem.core.base_model.BaseModel` class. At present a lot of
the abstract methods of the parent class (e.g.
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
from virtual_ecosystem.models.litter.carbon import (
    calculate_decay_rates,
    calculate_post_consumption_pools,
    calculate_total_C_mineralised,
    calculate_updated_pools,
)
from virtual_ecosystem.models.litter.chemistry import LitterChemistry
from virtual_ecosystem.models.litter.constants import LitterConsts
from virtual_ecosystem.models.litter.inputs import LitterInputs


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
        "c_n_ratio_above_metabolic",
        "c_n_ratio_above_structural",
        "c_n_ratio_woody",
        "c_n_ratio_below_metabolic",
        "c_n_ratio_below_structural",
        "c_p_ratio_above_metabolic",
        "c_p_ratio_above_structural",
        "c_p_ratio_woody",
        "c_p_ratio_below_metabolic",
        "c_p_ratio_below_structural",
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
        "c_n_ratio_above_metabolic",
        "c_n_ratio_above_structural",
        "c_n_ratio_woody",
        "c_n_ratio_below_metabolic",
        "c_n_ratio_below_structural",
        "c_p_ratio_above_metabolic",
        "c_p_ratio_above_structural",
        "c_p_ratio_woody",
        "c_p_ratio_below_metabolic",
        "c_p_ratio_below_structural",
        "deadwood_production",
        "leaf_turnover",
        "fallen_non_propagule_c_mass",
        "root_turnover",
        "stem_lignin",
        "senesced_leaf_lignin",
        "plant_reproductive_tissue_lignin",
        "root_lignin",
        "deadwood_c_n_ratio",
        "leaf_turnover_c_n_ratio",
        "plant_reproductive_tissue_turnover_c_n_ratio",
        "root_turnover_c_n_ratio",
        "deadwood_c_p_ratio",
        "leaf_turnover_c_p_ratio",
        "plant_reproductive_tissue_turnover_c_p_ratio",
        "root_turnover_c_p_ratio",
        "herbivory_waste_leaf_carbon",
        "herbivory_waste_leaf_nitrogen",
        "herbivory_waste_leaf_phosphorus",
        "herbivory_waste_leaf_lignin",
        "litter_consumption_above_metabolic",
        "litter_consumption_above_structural",
        "litter_consumption_woody",
        "litter_consumption_below_metabolic",
        "litter_consumption_below_structural",
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
        "c_n_ratio_above_metabolic",
        "c_n_ratio_above_structural",
        "c_n_ratio_woody",
        "c_n_ratio_below_metabolic",
        "c_n_ratio_below_structural",
        "c_p_ratio_above_metabolic",
        "c_p_ratio_above_structural",
        "c_p_ratio_woody",
        "c_p_ratio_below_metabolic",
        "c_p_ratio_below_structural",
        "litter_C_mineralisation_rate",
        "litter_N_mineralisation_rate",
        "litter_P_mineralisation_rate",
    ),
    vars_populated_by_first_update=(
        "litter_C_mineralisation_rate",
        "litter_N_mineralisation_rate",
        "litter_P_mineralisation_rate",
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
        static: bool = False,
        **kwargs: Any,
    ):
        """Litter init function.

        The init function is used only to define class attributes. Any logic should be
        handeled in :fun:`~virtual_ecosystem.litter.litter_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.litter_chemistry: LitterChemistry
        """Litter chemistry object for tracking of litter pool chemistries."""
        self.model_constants: LitterConsts
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
        static = config["litter"]["static"]

        LOGGER.info(
            "Information required to initialise the litter model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            static=static,
            model_constants=model_constants,
        )

    def _setup(
        self,
        model_constants: LitterConsts = LitterConsts(),
        **kwargs: Any,
    ) -> None:
        """Method to setup the litter model specific data variables.

        Args:
            model_constants: Set of constants for the litter model.
            **kwargs: Further arguments to the setup method.
        """

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
            if np.any(self.data[pool] < 0):
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
            if np.any(self.data[lignin_prop] < 0) or np.any(self.data[lignin_prop] > 1):
                bad_proportions.append(lignin_prop)

        if bad_proportions:
            to_raise = InitialisationError(
                "Lignin proportions not between 0 and 1 found in: "
                f"{', '.join(bad_proportions)}",
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check that nutrient ratios are not negative
        nutrient_ratios = [
            "c_n_ratio_above_metabolic",
            "c_n_ratio_above_structural",
            "c_n_ratio_woody",
            "c_n_ratio_below_metabolic",
            "c_n_ratio_below_structural",
            "c_p_ratio_above_metabolic",
            "c_p_ratio_above_structural",
            "c_p_ratio_woody",
            "c_p_ratio_below_metabolic",
            "c_p_ratio_below_structural",
        ]
        negative_ratios = []
        for ratio in nutrient_ratios:
            if np.any(self.data[ratio] < 0):
                negative_ratios.append(ratio)

        if negative_ratios:
            to_raise = InitialisationError(
                f"Negative nutrient ratios found in: {', '.join(negative_ratios)}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.litter_chemistry = LitterChemistry(self.data, constants=model_constants)
        self.model_constants = model_constants

    def spinup(self) -> None:
        """Placeholder function to spin up the litter model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Calculate changes in the litter pools and use them to update the pools.

        This function first calculates the decay rates for each litter pool, as well as
        the total carbon mineralisation rate. Once this is done, plant inputs to each
        pool are calculated, and used to find the new mass and lignin concentration of
        each litter pool.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # Calculate the pool sizes after animal consumption has occurred, which then get
        # used then for subsequent calculations
        consumed_pools = calculate_post_consumption_pools(
            above_metabolic=self.data["litter_pool_above_metabolic"].to_numpy(),
            above_structural=self.data["litter_pool_above_structural"].to_numpy(),
            woody=self.data["litter_pool_woody"].to_numpy(),
            below_metabolic=self.data["litter_pool_below_metabolic"].to_numpy(),
            below_structural=self.data["litter_pool_below_structural"].to_numpy(),
            consumption_above_metabolic=self.data[
                "litter_consumption_above_metabolic"
            ].to_numpy(),
            consumption_above_structural=self.data[
                "litter_consumption_above_structural"
            ].to_numpy(),
            consumption_woody=self.data["litter_consumption_woody"].to_numpy(),
            consumption_below_metabolic=self.data[
                "litter_consumption_below_metabolic"
            ].to_numpy(),
            consumption_below_structural=self.data[
                "litter_consumption_below_structural"
            ].to_numpy(),
        )

        # Calculate the litter pool decay rates
        decay_rates = calculate_decay_rates(
            post_consumption_pools=consumed_pools,
            lignin_above_structural=self.data["lignin_above_structural"].to_numpy(),
            lignin_woody=self.data["lignin_woody"].to_numpy(),
            lignin_below_structural=self.data["lignin_below_structural"].to_numpy(),
            air_temperatures=self.data["air_temperature"],
            soil_temperatures=self.data["soil_temperature"],
            water_potentials=self.data["matric_potential"],
            layer_structure=self.layer_structure,
            constants=self.model_constants,
        )

        litter_inputs = LitterInputs.create_from_data(
            self.data, constants=self.model_constants
        )

        # Calculate the updated pool masses
        updated_pools = calculate_updated_pools(
            post_consumption_pools=consumed_pools,
            decay_rates=decay_rates,
            litter_inputs=litter_inputs,
            update_interval=self.model_timing.update_interval_quantity.to(
                "day"
            ).magnitude,
        )

        # Calculate all the litter chemistry changes
        updated_chemistries = self.litter_chemistry.calculate_new_pool_chemistries(
            updated_pools=updated_pools, litter_inputs=litter_inputs
        )

        # Calculate the total mineralisation rates from the litter
        total_C_mineralisation_rate = calculate_total_C_mineralised(
            decay_rates,
            model_constants=self.model_constants,
            core_constants=self.core_constants,
        )
        total_N_mineralisation_rate = self.litter_chemistry.calculate_N_mineralisation(
            decay_rates=decay_rates,
            active_microbe_depth=self.core_constants.max_depth_of_microbial_activity,
        )
        total_P_mineralisation_rate = self.litter_chemistry.calculate_P_mineralisation(
            decay_rates=decay_rates,
            active_microbe_depth=self.core_constants.max_depth_of_microbial_activity,
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
                updated_chemistries["lignin_above_structural"], dims="cell_id"
            ),
            "lignin_woody": updated_chemistries["lignin_woody"],
            "lignin_below_structural": updated_chemistries["lignin_below_structural"],
            "c_n_ratio_above_metabolic": updated_chemistries[
                "c_n_ratio_above_metabolic"
            ],
            "c_n_ratio_above_structural": updated_chemistries[
                "c_n_ratio_above_structural"
            ],
            "c_n_ratio_woody": updated_chemistries["c_n_ratio_woody"],
            "c_n_ratio_below_metabolic": updated_chemistries[
                "c_n_ratio_below_metabolic"
            ],
            "c_n_ratio_below_structural": updated_chemistries[
                "c_n_ratio_below_structural"
            ],
            "c_p_ratio_above_metabolic": updated_chemistries[
                "c_p_ratio_above_metabolic"
            ],
            "c_p_ratio_above_structural": updated_chemistries[
                "c_p_ratio_above_structural"
            ],
            "c_p_ratio_woody": updated_chemistries["c_p_ratio_woody"],
            "c_p_ratio_below_metabolic": updated_chemistries[
                "c_p_ratio_below_metabolic"
            ],
            "c_p_ratio_below_structural": updated_chemistries[
                "c_p_ratio_below_structural"
            ],
            "litter_C_mineralisation_rate": DataArray(
                total_C_mineralisation_rate, dims="cell_id"
            ),
            "litter_N_mineralisation_rate": DataArray(
                total_N_mineralisation_rate, dims="cell_id"
            ),
            "litter_P_mineralisation_rate": DataArray(
                total_P_mineralisation_rate, dims="cell_id"
            ),
        }

        # And then use then to update the litter variables
        self.data.add_from_dict(updated_litter_variables)

    def cleanup(self) -> None:
        """Placeholder function for litter model cleanup."""
