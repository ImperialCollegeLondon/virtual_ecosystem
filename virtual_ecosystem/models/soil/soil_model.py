"""The :mod:`~virtual_ecosystem.models.soil.soil_model` module creates a
:class:`~virtual_ecosystem.models.soil.soil_model.SoilModel` class as a child of the
:class:`~virtual_ecosystem.core.base_model.BaseModel` class. At present a lot of the
abstract methods of the parent class (e.g.
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
"""  # noqa: D205

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from xarray import DataArray, where

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents, LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.soil.constants import SoilConsts
from virtual_ecosystem.models.soil.microbial_groups import (
    EnzymeConstants,
    MicrobialGroupConstants,
    make_full_set_of_enzymes,
    make_full_set_of_microbial_groups,
)
from virtual_ecosystem.models.soil.pools import SoilPools


class IntegrationError(Exception):
    """Custom exception class for cases when model integration cannot be completed."""


class SoilModel(
    BaseModel,
    model_name="soil",
    model_update_bounds=("30 minutes", "3 months"),
    vars_required_for_init=(
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_bacteria",
        "soil_c_pool_fungi",
        "soil_c_pool_pom",
        "soil_c_pool_necromass",
        "soil_enzyme_pom_bacteria",
        "soil_enzyme_maom_bacteria",
        "soil_enzyme_pom_fungi",
        "soil_enzyme_maom_fungi",
        "soil_n_pool_don",
        "soil_n_pool_particulate",
        "soil_n_pool_necromass",
        "soil_n_pool_maom",
        "soil_n_pool_ammonium",
        "soil_n_pool_nitrate",
        "soil_p_pool_dop",
        "soil_p_pool_particulate",
        "soil_p_pool_necromass",
        "soil_p_pool_maom",
        "soil_p_pool_primary",
        "soil_p_pool_secondary",
        "soil_p_pool_labile",
        "pH",
        "bulk_density",
        "clay_fraction",
    ),
    vars_populated_by_init=(
        "dissolved_nitrate",
        "dissolved_ammonium",
        "dissolved_phosphorus",
    ),
    vars_required_for_update=(
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_bacteria",
        "soil_c_pool_fungi",
        "soil_c_pool_pom",
        "soil_c_pool_necromass",
        "soil_enzyme_pom_bacteria",
        "soil_enzyme_maom_bacteria",
        "soil_enzyme_pom_fungi",
        "soil_enzyme_maom_fungi",
        "soil_n_pool_don",
        "soil_n_pool_particulate",
        "soil_n_pool_necromass",
        "soil_n_pool_maom",
        "soil_n_pool_ammonium",
        "soil_n_pool_nitrate",
        "soil_p_pool_dop",
        "soil_p_pool_particulate",
        "soil_p_pool_necromass",
        "soil_p_pool_maom",
        "soil_p_pool_primary",
        "soil_p_pool_secondary",
        "soil_p_pool_labile",
        "matric_potential",
        "vertical_flow",
        "soil_temperature",
        "soil_moisture",
        "litter_C_mineralisation_rate",
        "litter_N_mineralisation_rate",
        "litter_P_mineralisation_rate",
        "nitrogen_fixation_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
    ),
    vars_updated=(
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_bacteria",
        "soil_c_pool_fungi",
        "soil_c_pool_pom",
        "soil_c_pool_necromass",
        "soil_enzyme_pom_bacteria",
        "soil_enzyme_maom_bacteria",
        "soil_enzyme_pom_fungi",
        "soil_enzyme_maom_fungi",
        "soil_n_pool_don",
        "soil_n_pool_particulate",
        "soil_n_pool_necromass",
        "soil_n_pool_maom",
        "soil_n_pool_ammonium",
        "soil_n_pool_nitrate",
        "soil_p_pool_dop",
        "soil_p_pool_particulate",
        "soil_p_pool_necromass",
        "soil_p_pool_maom",
        "soil_p_pool_primary",
        "soil_p_pool_secondary",
        "soil_p_pool_labile",
        "dissolved_nitrate",
        "dissolved_ammonium",
        "dissolved_phosphorus",
    ),
    vars_populated_by_first_update=(),
):
    """A class defining the soil model.

    This model can be configured based on the data object and a config dictionary. It
    can be updated by numerical integration. At present the underlying model this class
    wraps is quite simple (i.e. four soil carbon pools), but this will get more complex
    as the Virtual Ecosystem develops.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        static: bool = False,
        **kwargs: Any,
    ):
        """Soil init function.

        The init function is used only to define class attributes. Any logic should be
        handeled in :fun:`~virtual_ecosystem.soil.soil_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.model_constants: SoilConsts
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
        static = config["soil"]["static"]

        LOGGER.info(
            "Information required to initialise the soil model successfully extracted."
        )

        enzyme_classes = make_full_set_of_enzymes(config)
        microbial_groups = make_full_set_of_microbial_groups(
            config, enzyme_classes=enzyme_classes
        )

        return cls(
            data=data,
            core_components=core_components,
            static=static,
            model_constants=model_constants,
            microbial_groups=microbial_groups,
            enzyme_classes=enzyme_classes,
        )

    def _setup(
        self,
        model_constants: SoilConsts,
        microbial_groups: dict[str, MicrobialGroupConstants],
        enzyme_classes: dict[str, EnzymeConstants],
        **kwargs: Any,
    ) -> None:
        """Function to setup up the soil model."""

        # TODO - At the moment the soil model only cares about the very top layer. As
        # both the soil and abiotic models get more complex this might well change.
        self.model_constants = model_constants

        # Store microbial functional groups and enzyme classes needed by the model
        self.microbial_groups = microbial_groups
        self.enzyme_classes = enzyme_classes

        # Calculate dissolved amounts of each inorganic nutrient
        dissolved_nutrient_pools = self.calculate_dissolved_nutrient_concentrations()
        # Update the data object with these pools
        self.data.add_from_dict(dissolved_nutrient_pools)

        # Check that soil pool data is appropriately bounded
        if not self._all_pools_positive():
            to_raise = InitialisationError(
                "Initial carbon pools contain at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Update the soil model by integrating.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # Find carbon pool updates by integration
        updated_carbon_pools = self.integrate()

        # Update carbon pools (attributes and data object)
        # n.b. this also updates the data object automatically
        self.data.add_from_dict(updated_carbon_pools)

        # Calculate dissolved amounts of each inorganic nutrients
        dissolved_nutrient_pools = self.calculate_dissolved_nutrient_concentrations()
        # Update the data object with these pools
        self.data.add_from_dict(dissolved_nutrient_pools)

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""

    def _all_pools_positive(self) -> bool:
        """Checks if all soil pools values greater than or equal to zero.

        Returns:
            A bool specifying whether all pools updated by the model are positive or
            not.
        """

        all_positive = True

        for var in self.vars_updated:
            if np.any(self.data[var] < 0.0):
                all_positive = False

        return all_positive

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
                if name in self.vars_updated and name not in self.vars_populated_by_init
            ]
        )

        # Find and store order of pools
        delta_pools_ordered = {
            name: np.array([])
            for name in map(str, self.data.data.keys())
            if name in self.vars_updated and name not in self.vars_populated_by_init
        }

        # Carry out simulation
        output = solve_ivp(
            construct_full_soil_model,
            t_span,
            y0,
            args=(
                self.data,
                no_cells,
                self.layer_structure,
                delta_pools_ordered,
                self.model_constants,
                self.microbial_groups,
                self.enzyme_classes,
                self.core_constants.max_depth_of_microbial_activity,
                self.core_constants.soil_moisture_capacity,
                self.layer_structure.soil_layer_thickness[0],
            ),
        )

        # Check if integration failed
        if not output.success:
            LOGGER.error(
                "Integration of soil module failed with following message: {}".format(  # noqa: UP032
                    str(output.message)
                )
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

    def calculate_dissolved_nutrient_concentrations(self) -> dict[str, DataArray]:
        """Calculate the amount of each inorganic nutrient that is in dissolved form.

        This calculates the nutrient concentration of the water in the topsoil layer.
        Negative values are explicitly handled by this function to prevent them from
        passing from the soil model (where they are unavoidable) into the plants model
        (where they could break things). When soil nutrient concentrations are negative
        it is assumed dissolved nutrient concentrations are taken to be zero.

        Returns:
            A data array containing the size of each dissolved nutrient pool [kg
            nutrient m^-3].
        """

        return {
            "dissolved_nitrate": where(
                self.data["soil_n_pool_nitrate"] >= 0.0,
                self.model_constants.solubility_coefficient_nitrate
                * self.data["soil_n_pool_nitrate"],
                0.0,
            ),
            "dissolved_ammonium": where(
                self.data["soil_n_pool_ammonium"] >= 0.0,
                self.model_constants.solubility_coefficient_ammonium
                * self.data["soil_n_pool_ammonium"],
                0.0,
            ),
            "dissolved_phosphorus": where(
                self.data["soil_p_pool_labile"] >= 0.0,
                self.model_constants.solubility_coefficient_labile_p
                * self.data["soil_p_pool_labile"],
                0.0,
            ),
        }


def construct_full_soil_model(
    t: float,
    pools: NDArray[np.float32],
    data: Data,
    no_cells: int,
    layer_structure: LayerStructure,
    delta_pools_ordered: dict[str, NDArray[np.float32]],
    model_constants: SoilConsts,
    functional_groups: dict[str, MicrobialGroupConstants],
    enzyme_classes: dict[str, EnzymeConstants],
    max_depth_of_microbial_activity: float,
    soil_moisture_capacity: float,
    top_soil_layer_thickness: float,
) -> NDArray[np.float32]:
    """Function that constructs the full soil model in a solve_ivp friendly form.

    Args:
        t: Current time [days]. At present the model has no explicit time dependence,
            but the function must still be accept a time value to allow it to be
            integrated.
        pools: An array containing all soil pools in a single vector
        data: The data object, used to populate the arguments i.e. pH and bulk density
        no_cells: Number of grid cells the integration is being performed over
        layer_structure: The details of the layer structure used across the Virtual
            Ecosystem.
        delta_pools_ordered: Dictionary to store pool changes in the order that pools
            are stored in the initial condition vector.
        model_constants: Set of constants for the soil model.
        functional_groups: Set of microbial functional groups used by the soil model.
        enzyme_classes: Set of enzyme classes used by the soil model.
        max_depth_of_microbial_activity: Maximum depth of the soil profile where
            microbial activity occurs [m].
        soil_moisture_capacity: Soil moisture capacity, i.e. the maximum
            (volumetric) moisture the soil can hold [unitless].
        top_soil_layer_thickness: Thickness of the topsoil layer [mm].

    Returns:
        The rate of change for each soil pool
    """

    # Construct index slices
    slices = make_slices(no_cells, len(delta_pools_ordered))

    # Construct dictionary of numpy arrays (using a for loop)
    all_pools = {
        str(pool): pools[slc] for slc, pool in zip(slices, delta_pools_ordered.keys())
    }

    soil_pools = SoilPools(
        data,
        pools=all_pools,
        constants=model_constants,
        functional_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        max_depth_of_microbial_activity=max_depth_of_microbial_activity,
    )

    return soil_pools.calculate_all_pool_updates(
        delta_pools_ordered=delta_pools_ordered,
        layer_structure=layer_structure,
        # TODO - This needs to be reconsidered as part of the soil-abiotic links review
        soil_moisture_capacity=soil_moisture_capacity,
        top_soil_layer_thickness=top_soil_layer_thickness,
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
