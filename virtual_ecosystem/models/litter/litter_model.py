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
from virtual_ecosystem.core.configuration import CompiledConfiguration
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
from virtual_ecosystem.models.litter.inputs import (
    LitterInputs,
    calculate_input_chemistries,
)
from virtual_ecosystem.models.litter.losses import calculate_litter_losses
from virtual_ecosystem.models.litter.model_config import (
    LitterConfiguration,
    LitterConstants,
)


class LitterModel(
    BaseModel,
    model_name="litter",
    model_update_bounds=("30 minutes", "3 months"),
    vars_required_for_init=(
        "litter_pool_above_metabolic_cnp",
        "litter_pool_above_structural_cnp",
        "litter_pool_woody_cnp",
        "litter_pool_below_metabolic_cnp",
        "litter_pool_below_structural_cnp",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
    ),
    vars_populated_by_init=(),
    vars_required_for_update=(
        "litter_pool_above_metabolic_cnp",
        "litter_pool_above_structural_cnp",
        "litter_pool_woody_cnp",
        "litter_pool_below_metabolic_cnp",
        "litter_pool_below_structural_cnp",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
        "stem_turnover_cnp",
        "root_turnover_cnp",
        "foliage_turnover_cnp",
        "stem_lignin",
        "senesced_leaf_lignin",
        "root_lignin",
        "herbivory_waste_leaf_cnp",
        "herbivory_waste_leaf_lignin",
        "litter_consumed_above_metabolic_cnp",
        "litter_consumed_above_structural_cnp",
        "litter_consumed_woody_cnp",
        "litter_consumed_below_metabolic_cnp",
        "litter_consumed_below_structural_cnp",
        "air_temperature",
        "soil_temperature",
        "matric_potential",
    ),
    vars_updated=(
        "litter_pool_above_metabolic_cnp",
        "litter_pool_above_structural_cnp",
        "litter_pool_woody_cnp",
        "litter_pool_below_metabolic_cnp",
        "litter_pool_below_structural_cnp",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
        "litter_mineralisation_rate_cnp",
    ),
    vars_populated_by_first_update=("litter_mineralisation_rate_cnp",),
):
    """A class defining the litter model.

    This model can be configured based on the data object and a config dictionary. At
    present the underlying model this class wraps is quite simple (i.e. two litter
    pools), but this will get more complex as the Virtual Ecosystem develops.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        model_constants: Set of constants for the litter model.
        static: Boolean flag indicating if the model should run in static mode.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: LitterConstants = LitterConstants(),
        static: bool = False,
    ):
        """Litter init function.

        The init function is used only to define class attributes. Any logic should be
        handled in :fun:`~virtual_ecosystem.litter.litter_model._setup`.
        """

        super().__init__(data, core_components, static)

        self.litter_chemistry: LitterChemistry
        """Litter chemistry object for tracking of litter pool chemistries."""
        self.model_constants: LitterConstants
        """Set of constants for the litter model."""

        # Run the setup if the model is not in deep static mode
        if self._run_setup:
            self._setup(
                model_constants=model_constants,
            )

    def _setup(
        self,
        model_constants: LitterConstants = LitterConstants(),
    ) -> None:
        """Method to setup the litter model specific data variables.

        See __init__ for argument descriptions.
        """

        # Check that no litter pool is negative
        all_pools = [
            "litter_pool_above_metabolic_cnp",
            "litter_pool_above_structural_cnp",
            "litter_pool_woody_cnp",
            "litter_pool_below_metabolic_cnp",
            "litter_pool_below_structural_cnp",
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

        self.litter_chemistry = LitterChemistry(self.data)
        self.model_constants = model_constants

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
    ) -> LitterModel:
        """Factory function to initialise the litter model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
        """

        # Extract the validated model configuration from the complete compiled
        # configuration. This syntax is odd but required to support static typing
        model_configuration: LitterConfiguration = configuration.get_subconfiguration(
            "litter", LitterConfiguration
        )

        LOGGER.info(
            "Information required to initialise the litter model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            static=model_configuration.static,
            model_constants=model_configuration.constants,
        )

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
            above_metabolic=self.data["litter_pool_above_metabolic_cnp"],
            above_structural=self.data["litter_pool_above_structural_cnp"],
            woody=self.data["litter_pool_woody_cnp"],
            below_metabolic=self.data["litter_pool_below_metabolic_cnp"],
            below_structural=self.data["litter_pool_below_structural_cnp"],
            consumption_above_metabolic=self.data[
                "litter_consumed_above_metabolic_cnp"
            ],
            consumption_above_structural=self.data[
                "litter_consumed_above_structural_cnp"
            ],
            consumption_woody=self.data["litter_consumed_woody_cnp"],
            consumption_below_metabolic=self.data[
                "litter_consumed_below_metabolic_cnp"
            ],
            consumption_below_structural=self.data[
                "litter_consumed_below_structural_cnp"
            ],
            cell_area=self.data.grid.cell_area,
        )

        # Calculate the litter pool decay rates
        decay_rates = calculate_decay_rates(
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
            self.data,
            constants=self.model_constants,
            update_interval=self.model_timing.update_interval_quantity.to(
                "days"
            ).magnitude,
        )

        input_chemistries = calculate_input_chemistries(
            litter_inputs=litter_inputs,
            meta_to_struct_nitrogen_ratio=self.model_constants.metabolic_to_structural_n_ratio,
            meta_to_struct_phosphorus_ratio=self.model_constants.metabolic_to_structural_p_ratio,
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

        litter_losses = calculate_litter_losses(
            original_pools=consumed_pools,
            final_pools=updated_pools,
            litter_inputs=litter_inputs,
            input_chemistries=input_chemistries,
            data=self.data,
            update_interval=self.model_timing.update_interval_quantity.to(
                "day"
            ).magnitude,
            active_microbe_depth=self.core_constants.max_depth_of_microbial_activity,
        )

        # Calculate all the litter chemistry changes
        updated_chemistries = self.litter_chemistry.calculate_new_pool_chemistries(
            litter_inputs=litter_inputs,
            litter_losses=litter_losses,
            input_chemistries=input_chemistries,
            original_pools=consumed_pools,
            update_interval=self.model_timing.update_interval_quantity.to(
                "day"
            ).magnitude,
        )

        # Calculate the total carbon mineralisation rate from the litter
        total_C_mineralisation_rate = calculate_total_C_mineralised(
            litter_losses=litter_losses,
            model_constants=self.model_constants,
            core_constants=self.core_constants,
            update_interval=self.model_timing.update_interval_quantity.to(
                "day"
            ).magnitude,
        )

        # Construct dictionary of data arrays to return
        updated_litter_variables = {
            "litter_pool_above_metabolic_cnp": DataArray(
                np.stack(
                    [
                        updated_pools["above_metabolic"],
                        updated_chemistries["above_metabolic_nitrogen"],
                        updated_chemistries["above_metabolic_phosphorus"],
                    ],
                    axis=1,
                ),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
            "litter_pool_above_structural_cnp": DataArray(
                np.stack(
                    [
                        updated_pools["above_structural"],
                        updated_chemistries["above_structural_nitrogen"],
                        updated_chemistries["above_structural_phosphorus"],
                    ],
                    axis=1,
                ),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
            "litter_pool_woody_cnp": DataArray(
                np.stack(
                    [
                        updated_pools["woody"],
                        updated_chemistries["woody_nitrogen"],
                        updated_chemistries["woody_phosphorus"],
                    ],
                    axis=1,
                ),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
            "litter_pool_below_metabolic_cnp": DataArray(
                np.stack(
                    [
                        updated_pools["below_metabolic"],
                        updated_chemistries["below_metabolic_nitrogen"],
                        updated_chemistries["below_metabolic_phosphorus"],
                    ],
                    axis=1,
                ),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
            "litter_pool_below_structural_cnp": DataArray(
                np.stack(
                    [
                        updated_pools["below_structural"],
                        updated_chemistries["below_structural_nitrogen"],
                        updated_chemistries["below_structural_phosphorus"],
                    ],
                    axis=1,
                ),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
            "lignin_above_structural": DataArray(
                updated_chemistries["lignin_above_structural"], dims="cell_id"
            ),
            "lignin_woody": DataArray(
                updated_chemistries["lignin_woody"], dims="cell_id"
            ),
            "lignin_below_structural": DataArray(
                updated_chemistries["lignin_below_structural"], dims="cell_id"
            ),
            "litter_mineralisation_rate_cnp": DataArray(
                data=np.stack(
                    (
                        total_C_mineralisation_rate,
                        litter_losses.N_mineralisation_rate,
                        litter_losses.P_mineralisation_rate,
                    ),
                    axis=1,
                ),
                coords={"cell_id": self.data["cell_id"], "element": ["C", "N", "P"]},
            ),
        }

        # And then use then to update the litter variables
        self.data.add_from_dict(updated_litter_variables)

    def cleanup(self) -> None:
        """Placeholder function for litter model cleanup."""
