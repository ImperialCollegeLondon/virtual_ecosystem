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
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents, LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConfiguration, CoreConstants
from virtual_ecosystem.models.hydrology.model_config import (
    HydrologyConfiguration,
)
from virtual_ecosystem.models.litter.env_factors import (
    average_temperature_over_microbially_active_layers,
    average_water_potential_over_microbially_active_layers,
)
from virtual_ecosystem.models.soil.env_factors import (
    EnvironmentalEffectFactors,
    calculate_environmental_effect_factors,
)
from virtual_ecosystem.models.soil.microbial_groups import (
    MicrobialGroupConstants,
    make_full_set_of_microbial_groups,
)
from virtual_ecosystem.models.soil.model_config import (
    SoilConfiguration,
    SoilConstants,
    SoilEnzymeClass,
)
from virtual_ecosystem.models.soil.pools import (
    SoilPools,
    calculate_maintenance_biomass_synthesis,
)
from virtual_ecosystem.models.soil.uptake import calculate_maximum_uptake_rates


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
        "soil_c_pool_saprotrophic_fungi",
        "soil_c_pool_arbuscular_mycorrhiza",
        "soil_c_pool_ectomycorrhiza",
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
        "clay_fraction",
        "matric_potential",
        "mean_annual_temperature",
    ),
    vars_populated_by_init=(
        "dissolved_nitrate",
        "dissolved_ammonium",
        "dissolved_phosphorus",
        "ecto_supply_limit_n",
        "ecto_supply_limit_p",
        "arbuscular_supply_limit_n",
        "arbuscular_supply_limit_p",
        "production_of_fungal_fruiting_bodies",
    ),
    vars_required_for_update=(
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_bacteria",
        "soil_c_pool_saprotrophic_fungi",
        "soil_c_pool_arbuscular_mycorrhiza",
        "soil_c_pool_ectomycorrhiza",
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
        "clay_fraction",
        "matric_potential",
        "vertical_flow",
        "soil_temperature",
        "air_temperature",
        "soil_moisture",
        "litter_C_mineralisation_rate",
        "litter_N_mineralisation_rate",
        "litter_P_mineralisation_rate",
        "plant_symbiote_carbon_supply",
        "root_carbohydrate_exudation",
        "plant_ammonium_uptake",
        "plant_nitrate_uptake",
        "plant_phosphorus_uptake",
        "plant_n_uptake_arbuscular",
        "plant_n_uptake_ecto",
        "plant_p_uptake_arbuscular",
        "plant_p_uptake_ecto",
        "subcanopy_ammonium_uptake",
        "subcanopy_nitrate_uptake",
        "subcanopy_phosphorus_uptake",
        "animal_pom_consumption_carbon",
        "animal_pom_consumption_nitrogen",
        "animal_pom_consumption_phosphorus",
        "animal_bacteria_consumption",
        "animal_saprotrophic_fungi_consumption",
        "animal_ectomycorrhiza_consumption",
        "animal_arbuscular_mycorrhiza_consumption",
        "decay_of_fungal_fruiting_bodies",
    ),
    vars_updated=(
        "soil_c_pool_maom",
        "soil_c_pool_lmwc",
        "soil_c_pool_bacteria",
        "soil_c_pool_saprotrophic_fungi",
        "soil_c_pool_arbuscular_mycorrhiza",
        "soil_c_pool_ectomycorrhiza",
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
        "ecto_supply_limit_n",
        "ecto_supply_limit_p",
        "arbuscular_supply_limit_n",
        "arbuscular_supply_limit_p",
        "production_of_fungal_fruiting_bodies",
    ),
    # TODO - If anything gets added to this section the implementation docs will need to
    # be updated
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
        handled in :fun:`~virtual_ecosystem.soil.soil_model._setup`.
        """

        super().__init__(
            data=data,
            core_components=core_components,
            static=static,
            **kwargs,
        )

        self.model_constants: SoilConstants
        """Set of constants for the soil model."""

        self.refreshed_variables = ["new_fungal_fruiting_body_production"]
        """List of variables that the model resets for each new integration step.
        
        These variables are intermediate values that it does not make sense to store in
        the data object.
        """

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
    ) -> SoilModel:
        """Factory function to initialise the soil model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Extract the required subconfigurations from the compiled configuration.
        soil_configuration: SoilConfiguration = configuration.get_subconfiguration(
            "soil", SoilConfiguration
        )
        core_configuration: CoreConfiguration = configuration.get_subconfiguration(
            "core", CoreConfiguration
        )
        hydrology_configuration: HydrologyConfiguration = (
            configuration.get_subconfiguration("hydrology", HydrologyConfiguration)
        )

        LOGGER.info(
            "Information required to initialise the soil model successfully extracted."
        )

        # Extract enzyme classes to a dictionary
        enzyme_classes: dict[str, SoilEnzymeClass] = {
            f"{enzyme.source}_{enzyme.substrate}": enzyme
            for enzyme in soil_configuration.enzyme_class_definition
        }

        microbial_groups = make_full_set_of_microbial_groups(
            config=soil_configuration,
            enzyme_classes=enzyme_classes,
            core_constants=core_configuration.constants,
        )

        return cls(
            data=data,
            configuration=configuration,
            core_components=core_components,
            static=soil_configuration.static,
            model_constants=soil_configuration.constants,
            microbial_groups=microbial_groups,
            enzyme_classes=enzyme_classes,
            soil_moisture_saturation=hydrology_configuration.constants.soil_moisture_saturation,
            soil_moisture_residual=hydrology_configuration.constants.soil_moisture_residual,
        )

    def _setup(
        self,
        model_constants: SoilConstants,
        microbial_groups: dict[str, MicrobialGroupConstants],
        enzyme_classes: dict[str, SoilEnzymeClass],
        soil_moisture_saturation: float,
        soil_moisture_residual: float,
        **kwargs: Any,
    ) -> None:
        """Function to setup up the soil model."""

        self.model_constants = model_constants

        # Store microbial functional groups and enzyme classes needed by the model
        self.microbial_groups = microbial_groups
        self.enzyme_classes = enzyme_classes

        # Store the required hydrology constants
        self.soil_moisture_saturation = soil_moisture_saturation
        self.soil_moisture_residual = soil_moisture_residual

        # Calculate dissolved amounts of each inorganic nutrient
        dissolved_nutrient_pools = self.calculate_dissolved_nutrient_concentrations()
        # Update the data object with these pools
        self.data.add_from_dict(dissolved_nutrient_pools)

        # Calculate the limit on what the plants can take from the symbiotic microbes
        symbiotic_supply_limits = self.calculate_symbiotic_supply_limits(init=True)
        # Add these limits to the data object
        self.data.add_from_dict(symbiotic_supply_limits)

        # The initial production of fungal fruiting bodies is set to zero, because the
        # initial density estimate implicitly contains the initial production
        fungal_fruiting_body_production = {
            "production_of_fungal_fruiting_bodies": DataArray(
                np.zeros(self.data.grid.n_cells), dims="cell_id"
            )
        }
        self.data.add_from_dict(fungal_fruiting_body_production)

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
        updated_soil_pools = self.integrate()

        # Update carbon pools (attributes and data object) n.b. this also updates the
        # data object automatically. Refreshed variables have to be excluded from this
        self.data.add_from_dict(
            {
                variable: value
                for variable, value in updated_soil_pools.items()
                if variable not in self.refreshed_variables
            }
        )

        fruiting_body_production_rate = self.convert_fruiting_body_production_to_rate(
            total_production=updated_soil_pools["new_fungal_fruiting_body_production"]
        )
        self.data.add_from_dict(fruiting_body_production_rate)

        # Calculate dissolved amounts of each inorganic nutrients
        dissolved_nutrient_pools = self.calculate_dissolved_nutrient_concentrations()

        # Update the data object with these pools
        self.data.add_from_dict(dissolved_nutrient_pools)

        # Calculate the limit on what the plants can take from the symbiotic microbes
        symbiotic_supply_limits = self.calculate_symbiotic_supply_limits(init=False)

        # Add these limits to the data object
        self.data.add_from_dict(symbiotic_supply_limits)

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
            ValueError: If any of the variables used by the soil model have NaN values.
        """

        # Find number of grid cells integration is being performed over
        no_cells = self.data.grid.n_cells

        # Extract update interval (in units of number of days)
        update_time = self.model_timing.update_interval_quantity.to("days").magnitude
        t_span = (0.0, update_time)

        # Construct vector of initial values y0. Zeros are added to the end for all the
        # non-data object variables
        y0 = np.concatenate(
            (
                np.concatenate(
                    [
                        self.data[name].to_numpy()
                        for name in map(str, self.data.data.keys())
                        if name in self.vars_updated
                        and name not in self.vars_populated_by_init
                    ]
                ),
                np.zeros(len(self.refreshed_variables) * self.data.grid.n_cells),
            )
        )

        # Find and store order of pools (refreshed variables go at the end)
        delta_pools_ordered = {
            **{
                name: np.array([])
                for name in map(str, self.data.data.keys())
                if name in self.vars_updated and name not in self.vars_populated_by_init
            },
            **{name: np.array([]) for name in self.refreshed_variables},
        }

        # Check if any values used by the soil model integration have NaN values (these
        # can stall the integration)
        unexpected_nans = set()

        for var in self.vars_required_for_update:
            if self.check_for_unexpected_nan_values(var=var):
                unexpected_nans.add(var)

        if unexpected_nans:
            to_raise_nan = ValueError(
                "Soil model integration cannot proceed because the following "
                f"variables have unexpected NaN values: {unexpected_nans}"
            )
            LOGGER.error(to_raise_nan)
            raise to_raise_nan

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
                self.core_constants,
                self.soil_moisture_saturation,
                self.soil_moisture_residual,
                self.layer_structure.soil_layer_thickness[0],
            ),
        )

        # Check if integration failed
        if not output.success:
            to_raise = IntegrationError(
                "Integration of soil module failed with following message: "
                f"{output.message!s}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Construct index slices
        slices = make_slices(no_cells, round(len(y0) / no_cells))

        # Construct dictionary of data arrays
        new_c_pools = {
            str(pool): DataArray(output.y[slc, -1], dims="cell_id")
            for slc, pool in zip(slices, delta_pools_ordered.keys())
        }

        return new_c_pools

    def check_for_unexpected_nan_values(self, var: str) -> bool:
        """Check if there are unexpected NaN values in the data for a specific variable.

        The soil model needs the air_temperature variable to have non-NaN values at the
        soil surface, and the other layer structured variables to be defined for every
        soil layer. For these variables, this function takes the appropriate subset.

        Args:
            var: The name of the variable being checked

        Returns:
            Whether the data for the variable has any unexpected NaN values.
        """

        if var == "air_temperature":
            subset = self.data[var].isel(layers=self.layer_structure.index_surface)
        elif "layers" in self.data[var].dims:
            subset = self.data[var].isel(layers=self.layer_structure.index_all_soil)
        else:
            subset = self.data[var]

        return bool(subset.isnull().any())

    def convert_fruiting_body_production_to_rate(
        self, total_production: DataArray
    ) -> dict[str, DataArray]:
        """Convert total fungal fruiting body production into a rate are being produced.

        The soil model integration provides a total mass produced (per soil volume) over
        the integration time period. This method converts this into a rate, and into per
        area rather than soil volume terms.

        Args:
            total_production: The total production of fungal fruiting bodies over the
                integration time period, per volume of soil [kg C m^-3]

        Returns:
            A data array containing the rate at which fungal fruiting bodies are
            produced per unit area [kg C m^-2 day^-1].
        """

        return {
            "production_of_fungal_fruiting_bodies": total_production
            * self.core_constants.max_depth_of_microbial_activity
            / self.model_timing.update_interval_quantity.to("days").magnitude
        }

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

    def to_per_area(
        self, output_rate: float | NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Method to convert an soil model rates from per volume to per area units.

        Per area units are used by the plant model, so quantities returned to the plant
        model need to have their units converted to this.

        Args:
            output_rate: Rate of output to convert [kg m^-3 day^-1].

        Returns:
            Output rate converted to per area units [kg m^-2 day^-1].
        """

        if isinstance(output_rate, float):
            return np.array(
                output_rate * self.core_constants.max_depth_of_microbial_activity
            )
        else:
            return output_rate * self.core_constants.max_depth_of_microbial_activity

    def calculate_symbiotic_supply_limits(self, init: bool) -> dict[str, DataArray]:
        """Calculate supply limits of nutrients to plants by symbiotic microbes.

        These limits are calculated for each symbiote for each nutrient. If the limits
        are negative they are returned as zero to prevent negative uptake. The rates are
        converted from the per volume units used in the soil model, to the per area
        units used in the plant model.

        TODO - In model initialisation, the annual mean temperature is used as an
        estimate of the soil temperature as soil temperatures are not yet known. This
        issue won't be resolved until we have decided what we are doing about model spin
        up

        Args:
            init: A boolean specifying whether this function is being called as part of
               the model initialisation or as part of the model update.

        Returns:
            The maximum amount each nutrient (nitrogen and phosphorus) that plants can
            draw from each mycorrhizal partner (arbuscular mycorrhizal and
            ectomycorrhizal fungi) [kg m^-2 day^-1]
        """

        if not init:
            averaged_soil_temperature = (
                average_temperature_over_microbially_active_layers(
                    soil_temperatures=self.data["soil_temperature"],
                    surface_temperature=self.data["air_temperature"][
                        self.layer_structure.index_surface_scalar
                    ].to_numpy(),
                    layer_structure=self.layer_structure,
                )
            )
        else:
            # As soil temperature hasn't be calculated yet we assume that it matches the
            # mean annual temperature (a common assumption for deeper soil layers)
            averaged_soil_temperature = self.data["mean_annual_temperature"].to_numpy()

        # Average soil temperature and water potential over the microbially active
        # layers, and then use to calculate the environmental factors
        soil_water_potential = average_water_potential_over_microbially_active_layers(
            water_potentials=self.data["matric_potential"],
            layer_structure=self.layer_structure,
        )

        env_factors = calculate_environmental_effect_factors(
            soil_water_potential=soil_water_potential,
            pH=self.data["pH"].to_numpy(),
            clay_fraction=self.data["clay_fraction"].to_numpy(),
            constants=self.model_constants,
        )

        ecto_n_limit, ecto_p_limit = find_maximum_mycorrhizal_supply(
            soil_c_pool_lmwc=self.data["soil_c_pool_lmwc"].to_numpy(),
            soil_n_pool_don=self.data["soil_n_pool_don"].to_numpy(),
            soil_n_pool_ammonium=self.data["soil_n_pool_ammonium"].to_numpy(),
            soil_n_pool_nitrate=self.data["soil_n_pool_nitrate"].to_numpy(),
            soil_p_pool_dop=self.data["soil_p_pool_dop"].to_numpy(),
            soil_p_pool_labile=self.data["soil_p_pool_labile"].to_numpy(),
            microbe_pool_size=self.data["soil_c_pool_ectomycorrhiza"].to_numpy(),
            soil_temp=averaged_soil_temperature,
            microbial_group=self.microbial_groups["ectomycorrhiza"],
            env_factors=env_factors,
        )
        arbuscular_n_limit, arbuscular_p_limit = find_maximum_mycorrhizal_supply(
            soil_c_pool_lmwc=self.data["soil_c_pool_lmwc"].to_numpy(),
            soil_n_pool_don=self.data["soil_n_pool_don"].to_numpy(),
            soil_n_pool_ammonium=self.data["soil_n_pool_ammonium"].to_numpy(),
            soil_n_pool_nitrate=self.data["soil_n_pool_nitrate"].to_numpy(),
            soil_p_pool_dop=self.data["soil_p_pool_dop"].to_numpy(),
            soil_p_pool_labile=self.data["soil_p_pool_labile"].to_numpy(),
            microbe_pool_size=self.data["soil_c_pool_arbuscular_mycorrhiza"].to_numpy(),
            soil_temp=averaged_soil_temperature,
            microbial_group=self.microbial_groups["arbuscular_mycorrhiza"],
            env_factors=env_factors,
        )

        return {
            "ecto_supply_limit_n": where(
                DataArray(ecto_n_limit) >= 0.0,
                self.to_per_area(ecto_n_limit),
                0.0,
            ),
            "ecto_supply_limit_p": where(
                DataArray(ecto_p_limit) >= 0.0,
                self.to_per_area(ecto_p_limit),
                0.0,
            ),
            "arbuscular_supply_limit_n": where(
                DataArray(arbuscular_n_limit) >= 0.0,
                self.to_per_area(arbuscular_n_limit),
                0.0,
            ),
            "arbuscular_supply_limit_p": where(
                DataArray(arbuscular_p_limit) >= 0.0,
                self.to_per_area(arbuscular_p_limit),
                0.0,
            ),
        }


def find_maximum_mycorrhizal_supply(
    soil_c_pool_lmwc: NDArray[np.floating],
    soil_n_pool_don: NDArray[np.floating],
    soil_n_pool_ammonium: NDArray[np.floating],
    soil_n_pool_nitrate: NDArray[np.floating],
    soil_p_pool_dop: NDArray[np.floating],
    soil_p_pool_labile: NDArray[np.floating],
    microbe_pool_size: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    microbial_group: MicrobialGroupConstants,
    env_factors: EnvironmentalEffectFactors,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Find maximum amount of nutrients mycorrhizal fungi can supply to plant partners.

    The assumption underlying this function is that mycorrhizal fungi are prepared to
    supply nutrients to their plant partners up to the point where it causes them to
    lose biomass. So, this function calculates the nitrogen and phosphorus uptake rates
    required to balance biomass losses. This is then subtracted from the maximum
    possible nutrient uptake rates to determine the maximum amount of nutrients that
    mycorrhiza are prepared to supply to their plant partners.

    Args:
        soil_c_pool_lmwc: The amount of carbon in the labile mineral associated organic
            matter pool [kg C m^-3]
        soil_n_pool_don: The amount of nitrogen in the dissolved organic nitrogen pool
            [kg N m^-3]
        soil_n_pool_ammonium: Size of the soil ammonium pool [kg N m^-3]
        soil_n_pool_nitrate: Size of the soil nitrate pool [kg N m^-3]
        soil_p_pool_dop: The amount of phosphorus in the dissolved organic phosphorus
            pool [kg P m^-3]
        soil_p_pool_labile: Size of the labile phosphorus pool [kg P m^-3]
        microbe_pool_size: Size of the microbial pool of interest [kg C m^-3]
        soil_temp: Soil temperature [degrees C]
        microbial_group: Constants associated with the microbial group of interest.
        env_factors: Data class containing the various factors through which the
            environment effects soil cycling rates.

    Returns:
        A tuple containing the maximum rate that the mycorrhizal fungal group is
        prepared to supply nitrogen and phosphorus to their plant partners [kg m^-3
        day^-1].
    """

    # Find the nitrogen and phosphorus uptake rates required to balance biomass losses
    biomass_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=microbe_pool_size,
        soil_temp=soil_temp,
        microbial_group=microbial_group,
    )
    nitrogen_requirement = biomass_loss / microbial_group.c_n_ratio
    phosphorus_requirement = biomass_loss / microbial_group.c_p_ratio

    # Find maximum uptake rates, and sum nitrogen and phosphorus ones
    maximum_uptake_rates = calculate_maximum_uptake_rates(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        soil_n_pool_don=soil_n_pool_don,
        soil_n_pool_ammonium=soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_n_pool_nitrate,
        soil_p_pool_dop=soil_p_pool_dop,
        soil_p_pool_labile=soil_p_pool_labile,
        microbial_pool_size=microbe_pool_size,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        soil_temp=soil_temp,
        functional_group=microbial_group,
    )
    maximum_nitrogen_uptake = (
        maximum_uptake_rates.organic_nitrogen
        + maximum_uptake_rates.ammonium
        + maximum_uptake_rates.nitrate
    )
    maximum_phosphorus_uptake = (
        maximum_uptake_rates.organic_phosphorus
        + maximum_uptake_rates.inorganic_phosphorus
    )

    return (
        maximum_nitrogen_uptake - nitrogen_requirement,
        maximum_phosphorus_uptake - phosphorus_requirement,
    )


def construct_full_soil_model(
    t: float,
    pools: NDArray[np.floating],
    data: Data,
    no_cells: int,
    layer_structure: LayerStructure,
    delta_pools_ordered: dict[str, NDArray[np.floating]],
    model_constants: SoilConstants,
    functional_groups: dict[str, MicrobialGroupConstants],
    enzyme_classes: dict[str, SoilEnzymeClass],
    core_constants: CoreConstants,
    soil_moisture_saturation: float,
    soil_moisture_residual: float,
    top_soil_layer_thickness: float,
) -> NDArray[np.floating]:
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
        core_constants: Set of constants shared across all models.
        soil_moisture_saturation: :term:`soil moisture saturation`, i.e. the maximum
            (volumetric) moisture the soil can hold [unitless].
        soil_moisture_residual: :term:`soil moisture residual`, i.e. the minimum
            (volumetric) moisture the soil can hold [unitless].
        top_soil_layer_thickness: Thickness of the topsoil layer [m].

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
        model_constants=model_constants,
        functional_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        core_constants=core_constants,
    )

    return soil_pools.calculate_all_pool_updates(
        delta_pools_ordered=delta_pools_ordered,
        layer_structure=layer_structure,
        soil_moisture_saturation=soil_moisture_saturation,
        soil_moisture_residual=soil_moisture_residual,
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
