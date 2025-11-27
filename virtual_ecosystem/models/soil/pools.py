"""The ``models.soil.pools`` module simulates all soil pools for the Virtual
Ecosystem. At the moment five carbon pools are modelled (low molecular weight carbon
(LMWC), mineral associated organic matter (MAOM), microbial biomass, particulate organic
matter (POM), microbial necromass), as well as two enzyme pools (POM and MAOM) degrading
enzymes. Pools that track the nitrogen and phosphorus pools associated with each of the
carbon pools are also included, as well as inorganic nitrogen and phosphorus pools.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.constants import convert_temperature

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.hydrology.hydrology_tools import (
    calculate_effective_saturation,
)
from virtual_ecosystem.models.litter.env_factors import (
    average_temperature_over_microbially_active_layers,
    average_water_potential_over_microbially_active_layers,
)
from virtual_ecosystem.models.soil.env_factors import (
    EnvironmentalEffectFactors,
    calculate_denitrification_temperature_factor,
    calculate_environmental_effect_factors,
    calculate_nitrification_moisture_factor,
    calculate_nitrification_temperature_factor,
    calculate_solute_removal_by_soil_water,
    calculate_symbiotic_nitrogen_fixation_carbon_cost,
    calculate_temperature_effect_on_microbes,
    find_total_soil_moisture_for_microbially_active_depth,
    find_water_outflow_rates,
)
from virtual_ecosystem.models.soil.microbial_groups import (
    CarbonSupply,
    MicrobialGroupConstants,
    calculate_symbiotic_carbon_supply,
)
from virtual_ecosystem.models.soil.model_config import SoilConstants, SoilEnzymeClass
from virtual_ecosystem.models.soil.uptake import calculate_nutrient_uptake_rates


@dataclass
class MicrobialChanges:
    """Changes due to microbial uptake, biomass production and losses."""

    lmwc_uptake: NDArray[np.floating]
    """Total rate of microbial uptake of low molecular weight carbon.
    
    Units of [kg C m^-3 day^-1]."""

    don_uptake: NDArray[np.floating]
    """Total rate of microbial uptake of dissolved organic nitrogen.
    
    Units of [kg N m^-3 day^-1]."""

    ammonium_change: NDArray[np.floating]
    """Total change in the ammonium pool due to microbial activity [kg N m^-3 day^-1].
    
    This change arises from the balance of immobilisation and mineralisation of
    ammonium. A positive value indicates a net immobilisation (uptake) of ammonium."""

    nitrate_change: NDArray[np.floating]
    """Total change in the nitrate pool due to microbial activity [kg N m^-3 day^-1].

    This change arises from the balance of immobilisation and mineralisation of
    nitrate. A positive value indicates a net immobilisation (uptake) of nitrate."""

    dop_uptake: NDArray[np.floating]
    """Total rate of microbial uptake of dissolved organic phosphorus.
    
    Units of [kg P m^-3 day^-1]."""

    labile_p_change: NDArray[np.floating]
    """Total change in the labile inorganic phosphorus pool due to microbial activity.
    
    Units of [kg P m^-3 day^-1]. This change arises from the balance of immobilisation
    and mineralisation of labile P. A positive value indicates a net immobilisation
    (uptake) of P. """

    bacteria_change: NDArray[np.floating]
    """Rate of change of bacterial biomass pool [kg C m^-3 day^-1]."""

    saprotrophic_fungi_change: NDArray[np.floating]
    """Rate of change of saprotrophic fungal biomass pool [kg C m^-3 day^-1]."""

    arbuscular_mycorrhiza_change: NDArray[np.floating]
    """Rate of change of arbuscular mycorrhizal fungi biomass pool [kg C m^-3 day^-1].
    """

    ectomycorrhiza_change: NDArray[np.floating]
    """Rate of change of ectomycorrhizal fungi biomass pool [kg C m^-3 day^-1]."""

    pom_enzyme_bacteria_change: NDArray[np.floating]
    """Rate of change for the bacterially produced :term:`POM` degrading enzymes.

    Units of [kg C m^-3 day^-1].
    """

    maom_enzyme_bacteria_change: NDArray[np.floating]
    """Rate of change for the bacterially produced :term:`MAOM` degrading enzymes.
    
    Units of [kg C m^-3 day^-1].
    """

    pom_enzyme_fungi_change: NDArray[np.floating]
    """Rate of change for the fungally produced :term:`POM` degrading enzymes.

    Units of [kg C m^-3 day^-1].
    """

    maom_enzyme_fungi_change: NDArray[np.floating]
    """Rate of change for the fungally produced :term:`MAOM` degrading enzymes.
    
    Units of [kg C m^-3 day^-1].
    """

    necromass_generation: NDArray[np.floating]
    """Rate at which necromass is being produced [kg C m^-3 day^-1]."""

    necromass_n_flow: NDArray[np.floating]
    """Nitrogen flow associated with necromass generation [kg N m^-3 day^-1]."""

    necromass_p_flow: NDArray[np.floating]
    """Phosphorus flow associated with necromass generation [kg P m^-3 day^-1]."""

    fruiting_body_production: NDArray[np.floating]
    """Rate a which fungal fruiting bodies are being produced [kg C m^-3 day^-1]."""


@dataclass
class EnzymeMediatedRates:
    """Rates of each enzyme mediated transfer between pools."""

    pom_to_lmwc: NDArray[np.floating]
    """Rate of particulate organic matter decomposition to low molecular weight carbon.
    
    Units of [kg C m^-3 day^-1].
    """

    maom_to_lmwc: NDArray[np.floating]
    """Rate of mineral associated organic matter decomposition to LMWC.

    Units of [kg C m^-3 day^-1].
    """


@dataclass
class EnzymePoolChanges:
    """Changes to the different enzyme pools due to production and denaturation."""

    net_change_pom_bacteria: NDArray[np.floating]
    """Net change in the bacterially produced enzyme pool that breaks down :term:`POM`.
    
    Units of [kg C m^-3 day^-1]
    """

    net_change_maom_bacteria: NDArray[np.floating]
    """Net change in the bacterially produced enzyme pool that breaks down :term:`MAOM`.
    
    Units of [kg C m^-3 day^-1]
    """

    net_change_pom_fungi: NDArray[np.floating]
    """Net change in the fungally produced enzyme pool that breaks down :term:`POM`.
    
    Units of [kg C m^-3 day^-1]
    """

    net_change_maom_fungi: NDArray[np.floating]
    """Net change in the fungally produced enzyme pool that breaks down :term:`MAOM`.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_pom_bacteria: NDArray[np.floating]
    """Denaturation rate for the :term:`POM` degrading enzyme produced by bacteria.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_maom_bacteria: NDArray[np.floating]
    """Denaturation rate for the :term:`MAOM` degrading enzyme produced by bacteria.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_pom_fungi: NDArray[np.floating]
    """Denaturation rate for the :term:`POM` degrading enzyme produced by fungi.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_maom_fungi: NDArray[np.floating]
    """Denaturation rate for the :term:`MAOM` degrading enzyme produced by fungi.
    
    Units of [kg C m^-3 day^-1]
    """


@dataclass
class BiomassLosses:
    """Losses of biomass from each microbial functional group due to turnover."""

    bacteria: NDArray[np.floating]
    """Rate of loss of bacterial biomass [kg C m^-3 day^-1]."""

    saprotrophic_fungi: NDArray[np.floating]
    """Rate of loss of saprotrophic fungal biomass [kg C m^-3 day^-1]."""

    ectomycorrhiza: NDArray[np.floating]
    """Rate of loss of ectomycorrhizal fungal biomass [kg C m^-3 day^-1]."""

    arbuscular_mycorrhiza: NDArray[np.floating]
    """Rate of loss of arbuscular mycorrhizal fungal biomass [kg C m^-3 day^-1]."""


@dataclass
class WaterRemovalRates:
    """Rate at which each soluble nutrient pool is removed due to soil water flows."""

    lmwc: NDArray[np.floating]
    """Removal rate for the low molecular weight carbon pool [kg C m^-3 day^-1]."""

    don: NDArray[np.floating]
    """Loss of dissolved organic nitrogen due to LMWC removal [kg N m^-3 day^-1]."""

    dop: NDArray[np.floating]
    """Loss of dissolved organic phosphorus due to LMWC removal [kg P m^-3 day^-1]."""

    ammonium: NDArray[np.floating]
    """Removal rate for the soil ammonium pool [kg N m^-3 day^-1]."""

    nitrate: NDArray[np.floating]
    """Removal rate for the soil nitrate pool [kg N m^-3 day^-1]."""

    labile_P: NDArray[np.floating]
    """Removal rate for the labile inorganic phosphorus pool [kg P m^-3 day^-1]."""


@dataclass
class LitterMineralisationFluxes:
    """Fluxes into each soil pool due to mineralisation from litter model."""

    lmwc: NDArray[np.floating]
    """Mineralisation into the low molecular weight carbon pool [kg C m^-3 day^-1]."""

    pom: NDArray[np.floating]
    """Mineralisation into the particulate organic matter pool [kg C m^-3 day^-1]."""

    don: NDArray[np.floating]
    """Mineralisation into the dissolved organic nitrogen pool [kg N m^-3 day^-1]."""

    ammonium: NDArray[np.floating]
    """Mineralisation into the ammonium pool [kg N m^-3 day^-1]."""

    particulate_n: NDArray[np.floating]
    """Mineralisation into the particulate organic nitrogen pool [kg N m^-3 day^-1]."""

    dop: NDArray[np.floating]
    """Mineralisation into the dissolved organic phosphorus pool [kg P m^-3 day^-1]."""

    labile_p: NDArray[np.floating]
    """Mineralisation into the labile inorganic phosphorus pool [kg P m^-3 day^-1]."""

    particulate_p: NDArray[np.floating]
    """Mineralisation into the particulate organic phosphorus pool.
    
    Units of [kg P m^-3 day^-1].
    """


@dataclass
class PoolData:
    """Data class collecting the full set of soil pools updated by the soil model."""

    soil_c_pool_maom: NDArray[np.floating]
    """Mineral associated organic matter pool [kg C m^-3]."""

    soil_c_pool_lmwc: NDArray[np.floating]
    """Low molecular weight carbon pool [kg C m^-3]."""

    soil_c_pool_bacteria: NDArray[np.floating]
    """Bacterial biomass pool [kg C m^-3]."""

    soil_c_pool_saprotrophic_fungi: NDArray[np.floating]
    """Saprotrophic fungi biomass pool [kg C m^-3]."""

    soil_c_pool_arbuscular_mycorrhiza: NDArray[np.floating]
    """Arbuscular mycorrhizal fungi biomass pool [kg C m^-3]."""

    soil_c_pool_ectomycorrhiza: NDArray[np.floating]
    """Ectomycorrhizal fungi biomass pool [kg C m^-3]."""

    soil_c_pool_pom: NDArray[np.floating]
    """Particulate organic matter pool [kg C m^-3]."""

    soil_c_pool_necromass: NDArray[np.floating]
    """Microbial necromass pool [kg C m^-3]."""

    soil_enzyme_pom_bacteria: NDArray[np.floating]
    """Bacteria produced enzyme class which breaks down :term:`POM` [kg C m^-3]."""

    soil_enzyme_maom_bacteria: NDArray[np.floating]
    """Bacteria produced enzyme class which breaks down :term:`MAOM` [kg C m^-3]."""

    soil_enzyme_pom_fungi: NDArray[np.floating]
    """Fungi produced enzyme class which breaks down :term:`POM` [kg C m^-3]."""

    soil_enzyme_maom_fungi: NDArray[np.floating]
    """Fungi produced enzyme class which breaks down :term:`MAOM` [kg C m^-3]."""

    soil_n_pool_don: NDArray[np.floating]
    """Organic nitrogen content of the low molecular weight carbon pool [kg N m^-3].
    
    This also gets termed the dissolved organic nitrogen (DON) pool.
    """

    soil_n_pool_particulate: NDArray[np.floating]
    """Organic nitrogen content of the particulate organic matter pool [kg N m^-3]."""

    soil_n_pool_necromass: NDArray[np.floating]
    """Organic nitrogen content of the microbial necromass pool [kg N m^-3]."""

    soil_n_pool_maom: NDArray[np.floating]
    """Organic nitrogen content of the :term:`MAOM` pool [kg N m^-3]."""

    soil_n_pool_ammonium: NDArray[np.floating]
    r"""Soil ammonium (:math:`\ce{NH4+}`) pool [kg N m^-3]."""

    soil_n_pool_nitrate: NDArray[np.floating]
    r"""Soil nitrate (:math:`\ce{NO3-}`) pool [kg N m^-3]."""

    soil_p_pool_dop: NDArray[np.floating]
    """Organic phosphorus content of the low molecular weight carbon pool [kg P m^-3].
    
    This also gets termed the dissolved organic phosphorus (DOP) pool.
    """

    soil_p_pool_particulate: NDArray[np.floating]
    """Organic phosphorus content of the particulate organic matter pool [kg P m^-3]."""

    soil_p_pool_necromass: NDArray[np.floating]
    """Organic phosphorus content of the microbial necromass pool [kg P m^-3]."""

    soil_p_pool_maom: NDArray[np.floating]
    """Organic phosphorus content of the :term:`MAOM` pool [kg P m^-3]."""

    soil_p_pool_primary: NDArray[np.floating]
    """Primary mineral phosphorus pool [kg P m^-3]."""

    soil_p_pool_secondary: NDArray[np.floating]
    """Secondary (inorganic) mineral phosphorus pool [kg P m^-3]."""

    soil_p_pool_labile: NDArray[np.floating]
    """Inorganic labile phosphorus pool [kg P m^-3]."""

    new_fungal_fruiting_body_production: NDArray[np.floating]
    """Fungal fruiting biomass produced during simulation time step [kg C m^-3]."""


class SoilPools:
    """This class collects all the various soil pools so that they can be updated.

    This class contains a method to update all soil pools. As well as taking in the data
    object it also has to take in another dataclass containing the pools. This
    dictionary is modifiable by the integration algorithm whereas the data object will
    only be modified when the entire soil model simulation has finished.
    """

    def __init__(
        self,
        data: Data,
        pools: dict[str, NDArray[np.floating]],
        model_constants: SoilConstants,
        functional_groups: dict[str, MicrobialGroupConstants],
        enzyme_classes: dict[str, SoilEnzymeClass],
        core_constants: CoreConstants,
    ):
        self.data = data
        """The data object for the Virtual Ecosystem simulation."""

        self.pools = PoolData(**pools)
        """Pools which can change during the soil model update.
        
        These pools need to be added outside the data object otherwise the integrator
        cannot update them and the integration will fail.
        """
        self.model_constants = model_constants
        """Set of constants for the soil model."""

        self.core_constants = core_constants
        """Set of constants shared across all models in the Virtual Ecosystem."""

        self.functional_groups = functional_groups
        """Set of microbial functional groups used by the soil model."""

        self.enzyme_classes = enzyme_classes
        """Details of the enzyme classes used by the soil model."""

    def calculate_all_pool_updates(
        self,
        delta_pools_ordered: dict[str, NDArray[np.floating]],
        layer_structure: LayerStructure,
        soil_moisture_saturation: float,
        soil_moisture_residual: float,
        top_soil_layer_thickness: float,
    ) -> NDArray[np.floating]:
        """Calculate net change for all soil pools.

        This function calls lower level functions which calculate the transfers between
        pools. When all transfers have been calculated the net transfer is used to
        calculate the net change for each pool.

        The data that this function uses (which comes from the `data` object) is stored
        in a dictionary form. This becomes an issue as the `scipy` integrator used to
        integrate this function expects a `numpy` array, and if the order of variables
        changes in this array the integrator will generate nonsensical results. To
        prevent this from happening a dictionary (`delta_pools_ordered`) is supplied
        that contains all the variables that get integrated, this dictionary sets the
        order of variables in the output `numpy` array. As this dictionary is passed
        from :func:`~virtual_ecosystem.models.soil.soil_model.SoilModel.integrate` this
        ensures that the order is the same for the entire integration.

        Args:
            delta_pools_ordered: Dictionary to store pool changes in the order that
                pools are stored in the initial condition vector.
            layer_structure: The details of the layer structure used across the Virtual
                Ecosystem.
            soil_moisture_saturation: The :term:`soil moisture saturation` [unitless].
            soil_moisture_residual: The :term:`soil moisture residual` [unitless].
            top_soil_layer_thickness: Thickness of the topsoil layer [m].

        Returns:
            A vector containing net changes to each pool. Order [lmwc, maom].
        """

        # Find temperature, soil water potential and soil moisture values for the
        # microbially active depth
        soil_water_potential = average_water_potential_over_microbially_active_layers(
            water_potentials=self.data["matric_potential"],
            layer_structure=layer_structure,
        )
        soil_temperature = average_temperature_over_microbially_active_layers(
            soil_temperatures=self.data["soil_temperature"],
            surface_temperature=self.data["air_temperature"][
                layer_structure.index_surface_scalar
            ].to_numpy(),
            layer_structure=layer_structure,
        )
        soil_moisture = find_total_soil_moisture_for_microbially_active_depth(
            soil_moistures=self.data["soil_moisture"], layer_structure=layer_structure
        )
        # Calculate the effective saturation of the soil (soil moistures need to be
        # converted from mm to a unitless measure for this to work).
        effective_saturation = calculate_effective_saturation(
            soil_moisture=soil_moisture / (top_soil_layer_thickness * 1e3),
            soil_moisture_saturation=soil_moisture_saturation,
            soil_moisture_residual=soil_moisture_residual,
        )
        # Find supply rate to each plant symbiotic group
        carbon_supply = calculate_symbiotic_carbon_supply(
            total_plant_supply=self.to_per_volume(
                self.data["plant_symbiote_carbon_supply"].to_numpy()
            ),
            nitrogen_fixer_fraction=self.model_constants.nitrogen_fixer_supply_fraction,
            ectomycorrhiza_fraction=self.model_constants.ectomycorrhiza_supply_fraction,
        )

        # Find environmental factors which impact biogeochemical soil processes
        env_factors = calculate_environmental_effect_factors(
            soil_water_potential=soil_water_potential,
            pH=self.data["pH"].to_numpy(),
            clay_fraction=self.data["clay_fraction"].to_numpy(),
            constants=self.model_constants,
        )
        # find changes related to microbial uptake, growth and decay
        microbial_changes = calculate_microbial_changes(
            pools=self.pools,
            soil_temp=soil_temperature,
            env_factors=env_factors,
            constants=self.model_constants,
            microbial_groups=self.functional_groups,
            enzyme_classes=self.enzyme_classes,
            carbon_supply=carbon_supply,
            plant_n_uptake_arbuscular=self.to_per_volume(
                self.data["plant_n_uptake_arbuscular"].to_numpy()
            ),
            plant_p_uptake_arbuscular=self.to_per_volume(
                self.data["plant_p_uptake_arbuscular"].to_numpy()
            ),
            plant_n_uptake_ecto=self.to_per_volume(
                self.data["plant_n_uptake_ecto"].to_numpy()
            ),
            plant_p_uptake_ecto=self.to_per_volume(
                self.data["plant_p_uptake_ecto"].to_numpy()
            ),
        )
        # find changes driven by the enzyme pools
        enzyme_mediated = calculate_enzyme_mediated_rates(
            pools=self.pools,
            soil_temp=soil_temperature,
            env_factors=env_factors,
            enzyme_classes=self.enzyme_classes,
        )

        # Calculate nutrient removal due to water flows
        nutrient_removal_by_water = calculate_nutrient_removal_by_water(
            soil_c_pool_lmwc=self.pools.soil_c_pool_lmwc,
            soil_n_pool_don=self.pools.soil_n_pool_don,
            soil_p_pool_dop=self.pools.soil_p_pool_dop,
            soil_n_pool_ammonium=self.pools.soil_n_pool_ammonium,
            soil_n_pool_nitrate=self.pools.soil_n_pool_nitrate,
            soil_p_pool_labile=self.pools.soil_p_pool_labile,
            vertical_flow_rates=self.data["vertical_flow"].to_numpy(),
            soil_moisture=soil_moisture,
            layer_structure=layer_structure,
            constants=self.model_constants,
        )

        # Calculate transfers between the lmwc, necromass and maom pools
        maom_desorption_to_lmwc = calculate_maom_desorption(
            soil_c_pool_maom=self.pools.soil_c_pool_maom,
            desorption_rate_constant=self.model_constants.maom_desorption_rate,
        )

        necromass_decay_to_lmwc = calculate_necromass_breakdown(
            soil_c_pool_necromass=self.pools.soil_c_pool_necromass,
            necromass_decay_rate=self.model_constants.necromass_decay_rate,
        )

        necromass_sorption_to_maom = calculate_sorption_to_maom(
            soil_c_pool=self.pools.soil_c_pool_necromass,
            sorption_rate_constant=self.model_constants.necromass_sorption_rate,
        )
        lmwc_sorption_to_maom = calculate_sorption_to_maom(
            soil_c_pool=self.pools.soil_c_pool_lmwc,
            sorption_rate_constant=self.model_constants.lmwc_sorption_rate,
        )

        # Calculate the flux to each pool from litter mineralisation
        litter_mineralisation_flux = calculate_litter_mineralisation_fluxes(
            litter_C_mineralisation_rate=self.data[
                "litter_C_mineralisation_rate"
            ].to_numpy(),
            litter_N_mineralisation_rate=self.data[
                "litter_N_mineralisation_rate"
            ].to_numpy(),
            litter_P_mineralisation_rate=self.data[
                "litter_P_mineralisation_rate"
            ].to_numpy(),
            constants=self.model_constants,
        )

        # Find mineralisation rates from POM
        pom_n_mineralisation = calculate_soil_nutrient_mineralisation(
            pool_carbon=self.pools.soil_c_pool_pom,
            pool_nutrient=self.pools.soil_n_pool_particulate,
            breakdown_rate=enzyme_mediated.pom_to_lmwc,
        )
        pom_p_mineralisation = calculate_soil_nutrient_mineralisation(
            pool_carbon=self.pools.soil_c_pool_pom,
            pool_nutrient=self.pools.soil_p_pool_particulate,
            breakdown_rate=enzyme_mediated.pom_to_lmwc,
        )

        # Find nitrogen released by necromass breakdown/sorption
        necromass_outflows = find_necromass_nutrient_outflows(
            necromass_carbon=self.pools.soil_c_pool_necromass,
            necromass_nitrogen=self.pools.soil_n_pool_necromass,
            necromass_phosphorus=self.pools.soil_p_pool_necromass,
            necromass_decay=necromass_decay_to_lmwc,
            necromass_sorption=necromass_sorption_to_maom,
        )
        # Find net nitrogen transfer between maom and lmwc/don
        nutrient_transfers_maom_to_lmwc = (
            calculate_net_nutrient_transfers_from_maom_to_lmwc(
                lmwc_carbon=self.pools.soil_c_pool_lmwc,
                lmwc_nitrogen=self.pools.soil_n_pool_don,
                lmwc_phosphorus=self.pools.soil_p_pool_dop,
                maom_carbon=self.pools.soil_c_pool_maom,
                maom_nitrogen=self.pools.soil_n_pool_maom,
                maom_phosphorus=self.pools.soil_p_pool_maom,
                maom_breakdown=enzyme_mediated.maom_to_lmwc,
                maom_desorption=maom_desorption_to_lmwc,
                lmwc_sorption=lmwc_sorption_to_maom,
            )
        )

        # TODO - Gas fluxes from soil area plausible validation target, but with the
        # exception of ammonia need more work to extract. But functionality to do this
        # and save it to the data object is something to think about in future.

        # Calculate nitrification and denitrification rates
        nitrification_rate = calculate_rate_of_nitrification(
            soil_temp=soil_temperature,
            effective_saturation=effective_saturation,
            soil_n_pool_ammonium=self.pools.soil_n_pool_ammonium,
            constants=self.model_constants,
        )
        denitrification_rate = calculate_rate_of_denitrification(
            soil_temp=soil_temperature,
            effective_saturation=effective_saturation,
            soil_n_pool_nitrate=self.pools.soil_n_pool_nitrate,
            constants=self.model_constants,
        )

        # Calculate rate at which ammonium volatilises as ammonia
        ammonia_volatilisation_rate = np.where(
            self.pools.soil_n_pool_ammonium >= 0.0,
            self.model_constants.ammonia_volatilisation_rate_constant
            * self.pools.soil_n_pool_ammonium,
            0.0,
        )

        # Calculate rate at which nitrogen is fixed
        symbiotic_nitrogen_fixation = calculate_symbiotic_nitrogen_fixation(
            carbon_supply=carbon_supply.nitrogen_fixers,
            soil_temp=soil_temperature,
            constants=self.model_constants,
        )
        free_living_nitrogen_fixation = calculate_free_living_nitrogen_fixation(
            soil_temp=soil_temperature,
            fixation_at_reference=self.model_constants.free_living_N_fixation_reference_rate,
            reference_temperature=self.model_constants.free_living_N_fixation_reference_temp,
            q10_nitrogen_fixation=self.model_constants.free_living_N_fixation_q10_coefficent,
            active_depth=self.core_constants.max_depth_of_microbial_activity,
        )

        primary_phosphorus_breakdown = (
            self.model_constants.primary_phosphorus_breakdown_rate
            * self.pools.soil_p_pool_primary
        )
        net_formation_secondary_P = calculate_net_formation_of_secondary_P(
            soil_p_pool_labile=self.pools.soil_p_pool_labile,
            soil_p_pool_secondary=self.pools.soil_p_pool_secondary,
            secondary_p_breakdown_rate=self.model_constants.secondary_phosphorus_breakdown_rate,
            labile_p_sorption_rate=self.model_constants.labile_phosphorus_sorption_rate,
        )

        fungal_fruiting_body_decay = calculate_fungal_fruiting_body_decay(
            decay_rate=self.to_per_volume(
                self.data["decay_of_fungal_fruiting_bodies"].to_numpy()
            ),
            fungal_fruiting_body_c_n_ratio=self.core_constants.fungal_fruiting_bodies_c_n_ratio,
            fungal_fruiting_body_c_p_ratio=self.core_constants.fungal_fruiting_bodies_c_p_ratio,
        )

        # Determine net changes to the pools
        delta_pools_ordered["soil_c_pool_lmwc"] = (
            litter_mineralisation_flux.lmwc
            + self.to_per_volume(self.data["root_carbohydrate_exudation"].to_numpy())
            + enzyme_mediated.pom_to_lmwc
            + enzyme_mediated.maom_to_lmwc
            + maom_desorption_to_lmwc
            + necromass_decay_to_lmwc
            + fungal_fruiting_body_decay["carbon"]
            - microbial_changes.lmwc_uptake
            - lmwc_sorption_to_maom
            - nutrient_removal_by_water.lmwc
        )

        delta_pools_ordered["soil_c_pool_maom"] = (
            necromass_sorption_to_maom
            + lmwc_sorption_to_maom
            - enzyme_mediated.maom_to_lmwc
            - maom_desorption_to_lmwc
        )
        delta_pools_ordered["soil_c_pool_bacteria"] = (
            microbial_changes.bacteria_change
            - self.data["animal_bacteria_consumption"].to_numpy()
        )
        delta_pools_ordered["soil_c_pool_saprotrophic_fungi"] = (
            microbial_changes.saprotrophic_fungi_change
            - self.data["animal_saprotrophic_fungi_consumption"].to_numpy()
        )
        delta_pools_ordered["soil_c_pool_arbuscular_mycorrhiza"] = (
            microbial_changes.arbuscular_mycorrhiza_change
            - self.data["animal_arbuscular_mycorrhiza_consumption"].to_numpy()
        )
        delta_pools_ordered["soil_c_pool_ectomycorrhiza"] = (
            microbial_changes.ectomycorrhiza_change
            - self.data["animal_ectomycorrhiza_consumption"].to_numpy()
        )
        delta_pools_ordered["soil_c_pool_pom"] = (
            litter_mineralisation_flux.pom
            - enzyme_mediated.pom_to_lmwc
            - self.data["animal_pom_consumption_carbon"].to_numpy()
        )
        delta_pools_ordered["soil_c_pool_necromass"] = (
            microbial_changes.necromass_generation
            - necromass_decay_to_lmwc
            - necromass_sorption_to_maom
        )
        delta_pools_ordered["soil_enzyme_pom_bacteria"] = (
            microbial_changes.pom_enzyme_bacteria_change
        )
        delta_pools_ordered["soil_enzyme_maom_bacteria"] = (
            microbial_changes.maom_enzyme_bacteria_change
        )
        delta_pools_ordered["soil_enzyme_pom_fungi"] = (
            microbial_changes.pom_enzyme_fungi_change
        )
        delta_pools_ordered["soil_enzyme_maom_fungi"] = (
            microbial_changes.maom_enzyme_fungi_change
        )
        delta_pools_ordered["new_fungal_fruiting_body_production"] = (
            microbial_changes.fruiting_body_production
        )
        delta_pools_ordered["soil_n_pool_don"] = (
            litter_mineralisation_flux.don
            + pom_n_mineralisation
            + necromass_outflows["decay_nitrogen"]
            + nutrient_transfers_maom_to_lmwc["nitrogen"]
            + fungal_fruiting_body_decay["nitrogen"]
            - microbial_changes.don_uptake
            - nutrient_removal_by_water.don
        )
        delta_pools_ordered["soil_n_pool_particulate"] = (
            litter_mineralisation_flux.particulate_n
            - pom_n_mineralisation
            - self.data["animal_pom_consumption_nitrogen"].to_numpy()
        )
        delta_pools_ordered["soil_n_pool_necromass"] = (
            microbial_changes.necromass_n_flow
            - necromass_outflows["decay_nitrogen"]
            - necromass_outflows["sorption_nitrogen"]
        )
        delta_pools_ordered["soil_n_pool_maom"] = (
            necromass_outflows["sorption_nitrogen"]
            - nutrient_transfers_maom_to_lmwc["nitrogen"]
        )
        delta_pools_ordered["soil_n_pool_ammonium"] = (
            self.to_per_volume(self.model_constants.ammonium_deposition_rate)
            + litter_mineralisation_flux.ammonium
            + symbiotic_nitrogen_fixation
            + free_living_nitrogen_fixation
            - microbial_changes.ammonium_change
            - self.to_per_volume(self.data["plant_ammonium_uptake"].to_numpy())
            - self.to_per_volume(self.data["subcanopy_ammonium_uptake"].to_numpy())
            - nutrient_removal_by_water.ammonium
            - ammonia_volatilisation_rate
            - nitrification_rate
        )
        delta_pools_ordered["soil_n_pool_nitrate"] = (
            nitrification_rate
            - denitrification_rate
            - microbial_changes.nitrate_change
            - self.to_per_volume(self.data["plant_nitrate_uptake"].to_numpy())
            - self.to_per_volume(self.data["subcanopy_nitrate_uptake"].to_numpy())
            - nutrient_removal_by_water.nitrate
        )
        delta_pools_ordered["soil_p_pool_dop"] = (
            litter_mineralisation_flux.dop
            + pom_p_mineralisation
            + necromass_outflows["decay_phosphorus"]
            + nutrient_transfers_maom_to_lmwc["phosphorus"]
            + fungal_fruiting_body_decay["phosphorus"]
            - microbial_changes.dop_uptake
            - nutrient_removal_by_water.dop
        )
        delta_pools_ordered["soil_p_pool_particulate"] = (
            litter_mineralisation_flux.particulate_p
            - pom_p_mineralisation
            - self.data["animal_pom_consumption_phosphorus"].to_numpy()
        )
        delta_pools_ordered["soil_p_pool_necromass"] = (
            microbial_changes.necromass_p_flow
            - necromass_outflows["decay_phosphorus"]
            - necromass_outflows["sorption_phosphorus"]
        )
        delta_pools_ordered["soil_p_pool_maom"] = (
            necromass_outflows["sorption_phosphorus"]
            - nutrient_transfers_maom_to_lmwc["phosphorus"]
        )
        delta_pools_ordered["soil_p_pool_primary"] = (
            self.model_constants.tectonic_uplift_rate_phosphorus
            - primary_phosphorus_breakdown
        )
        delta_pools_ordered["soil_p_pool_secondary"] = net_formation_secondary_P
        delta_pools_ordered["soil_p_pool_labile"] = (
            litter_mineralisation_flux.labile_p
            + self.to_per_volume(self.model_constants.phosphorus_deposition_rate)
            + primary_phosphorus_breakdown
            - microbial_changes.labile_p_change
            - self.to_per_volume(self.data["plant_phosphorus_uptake"].to_numpy())
            - self.to_per_volume(self.data["subcanopy_phosphorus_uptake"].to_numpy())
            - net_formation_secondary_P
            - nutrient_removal_by_water.labile_P
        )

        # Create output array of pools in desired order
        return np.concatenate(list(delta_pools_ordered.values()))

    def to_per_volume(
        self, input_rate: float | NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Method to convert an external input rate from per area to per volume units.

        Args:
            input_rate: Rate of input to convert [kg m^-2 day^-1].

        Returns:
            Input rate converted to per volume (of the microbial active layer) units [kg
            m^-3 day^-1].
        """

        if isinstance(input_rate, float):
            return np.array(
                input_rate / self.core_constants.max_depth_of_microbial_activity
            )
        else:
            return input_rate / self.core_constants.max_depth_of_microbial_activity


def calculate_microbial_changes(
    pools: PoolData,
    soil_temp: NDArray[np.floating],
    env_factors: EnvironmentalEffectFactors,
    constants: SoilConstants,
    microbial_groups: dict[str, MicrobialGroupConstants],
    enzyme_classes: dict[str, SoilEnzymeClass],
    carbon_supply: CarbonSupply,
    plant_n_uptake_arbuscular: NDArray[np.floating],
    plant_p_uptake_arbuscular: NDArray[np.floating],
    plant_n_uptake_ecto: NDArray[np.floating],
    plant_p_uptake_ecto: NDArray[np.floating],
) -> MicrobialChanges:
    """Calculate the changes for the microbial biomass and enzyme pools.

    This function calculates the uptake of :term:`LMWC` and inorganic nutrients by the
    microbial biomass pool and uses this to calculate the net change in the pool. The
    net change in each enzyme pool is found, and finally the total rate at which
    necromass is created is found.

    Args:
        pools: Data class containing the various soil pools.
        soil_temp: soil temperature for each soil grid cell [degrees C]
        env_factors: Data class containing the various factors through which the
            environment effects soil cycling rates.
        constants: Set of constants for the soil model.
        microbial_groups: Set of microbial functional groups used by the soil model.
        enzyme_classes: Details of the enzyme classes used by the soil model.
        carbon_supply: The carbon supply to each symbiotic microbial partner [kg C m^-3
            day^-1]
        plant_n_uptake_arbuscular: The rate at which plants take up nitrogen from the
            arbuscular mycorrhizal fungi [kg N m^-3 day^-1].
        plant_p_uptake_arbuscular: The rate at which plants take up phosphorus from the
            arbuscular mycorrhizal fungi [kg P m^-3 day^-1].
        plant_n_uptake_ecto: The rate at which plants take up nitrogen from the
            ectomycorrhizal fungi [kg N m^-3 day^-1].
        plant_p_uptake_ecto: The rate at which plants take up phosphorus from the
            ectomycorrhizal fungi [kg P m^-3 day^-1].

    Returns:
        A dataclass containing the rate at which microbes uptake LMWC, DON and DOP, and
        the rate of change in the microbial biomass pool and the enzyme pools.
    """

    # Calculate uptake, growth rate, and loss rate
    bacterial_growth, bacterial_uptake = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=pools.soil_c_pool_lmwc,
        soil_n_pool_don=pools.soil_n_pool_don,
        soil_n_pool_ammonium=pools.soil_n_pool_ammonium,
        soil_n_pool_nitrate=pools.soil_n_pool_nitrate,
        soil_p_pool_dop=pools.soil_p_pool_dop,
        soil_p_pool_labile=pools.soil_p_pool_labile,
        microbial_pool_size=pools.soil_c_pool_bacteria,
        external_carbon_supply=None,
        nitrogen_exchange=None,
        phosphorus_exchange=None,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        soil_temp=soil_temp,
        constants=constants,
        functional_group=microbial_groups["bacteria"],
    )
    saprotrophic_fungal_growth, saprotrophic_fungal_uptake = (
        calculate_nutrient_uptake_rates(
            soil_c_pool_lmwc=pools.soil_c_pool_lmwc,
            soil_n_pool_don=pools.soil_n_pool_don,
            soil_n_pool_ammonium=pools.soil_n_pool_ammonium,
            soil_n_pool_nitrate=pools.soil_n_pool_nitrate,
            soil_p_pool_dop=pools.soil_p_pool_dop,
            soil_p_pool_labile=pools.soil_p_pool_labile,
            microbial_pool_size=pools.soil_c_pool_saprotrophic_fungi,
            external_carbon_supply=None,
            nitrogen_exchange=None,
            phosphorus_exchange=None,
            water_factor=env_factors.water,
            pH_factor=env_factors.pH,
            soil_temp=soil_temp,
            constants=constants,
            functional_group=microbial_groups["saprotrophic_fungi"],
        )
    )
    arbuscular_mycorrhizal_growth, arbuscular_mycorrhizal_uptake = (
        calculate_nutrient_uptake_rates(
            soil_c_pool_lmwc=pools.soil_c_pool_lmwc,
            soil_n_pool_don=pools.soil_n_pool_don,
            soil_n_pool_ammonium=pools.soil_n_pool_ammonium,
            soil_n_pool_nitrate=pools.soil_n_pool_nitrate,
            soil_p_pool_dop=pools.soil_p_pool_dop,
            soil_p_pool_labile=pools.soil_p_pool_labile,
            microbial_pool_size=pools.soil_c_pool_arbuscular_mycorrhiza,
            external_carbon_supply=carbon_supply.arbuscular_mycorrhiza,
            nitrogen_exchange=plant_n_uptake_arbuscular,
            phosphorus_exchange=plant_p_uptake_arbuscular,
            water_factor=env_factors.water,
            pH_factor=env_factors.pH,
            soil_temp=soil_temp,
            constants=constants,
            functional_group=microbial_groups["arbuscular_mycorrhiza"],
        )
    )
    ectomycorrhizal_growth, ectomycorrhizal_uptake = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=pools.soil_c_pool_lmwc,
        soil_n_pool_don=pools.soil_n_pool_don,
        soil_n_pool_ammonium=pools.soil_n_pool_ammonium,
        soil_n_pool_nitrate=pools.soil_n_pool_nitrate,
        soil_p_pool_dop=pools.soil_p_pool_dop,
        soil_p_pool_labile=pools.soil_p_pool_labile,
        microbial_pool_size=pools.soil_c_pool_ectomycorrhiza,
        external_carbon_supply=carbon_supply.ectomycorrhiza,
        nitrogen_exchange=plant_n_uptake_ecto,
        phosphorus_exchange=plant_p_uptake_ecto,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        soil_temp=soil_temp,
        constants=constants,
        functional_group=microbial_groups["ectomycorrhiza"],
    )

    biomass_losses = calculate_biomass_losses(
        pools=pools, microbial_groups=microbial_groups, soil_temp=soil_temp
    )

    # Collect growth rates into a single dictionary
    growth_rates = {
        "bacteria": bacterial_growth,
        "saprotrophic_fungi": saprotrophic_fungal_growth,
        "arbuscular_mycorrhiza": np.where(
            arbuscular_mycorrhizal_growth > 0, arbuscular_mycorrhizal_growth, 0
        ),
        "ectomycorrhiza": np.where(
            ectomycorrhizal_growth > 0, ectomycorrhizal_growth, 0
        ),
    }

    # Calculate the total production of each enzyme class
    enzyme_production = calculate_enzyme_production(
        microbial_groups=microbial_groups, growth_rates=growth_rates
    )

    # Find changes in each enzyme pool
    enzyme_changes = calculate_enzyme_changes(
        pools=pools,
        enzyme_production=enzyme_production,
        enzyme_classes=enzyme_classes,
    )

    # Find flow of nitrogen to necromass pool
    necromass_n_flow, necromass_p_flow = calculate_nutrient_flows_to_necromass(
        biomass_losses=biomass_losses,
        enzyme_changes=enzyme_changes,
        microbial_groups=microbial_groups,
        enzyme_classes=enzyme_classes,
    )

    fungal_fruiting_body_production = calculate_fruiting_body_production(
        microbial_groups=microbial_groups, growth_rates=growth_rates
    )

    return MicrobialChanges(
        lmwc_uptake=bacterial_uptake.carbon
        + saprotrophic_fungal_uptake.carbon
        + arbuscular_mycorrhizal_uptake.carbon
        + ectomycorrhizal_uptake.carbon,
        don_uptake=bacterial_uptake.organic_nitrogen
        + saprotrophic_fungal_uptake.organic_nitrogen
        + arbuscular_mycorrhizal_uptake.organic_nitrogen
        + ectomycorrhizal_uptake.organic_nitrogen,
        ammonium_change=bacterial_uptake.ammonium
        + saprotrophic_fungal_uptake.ammonium
        + arbuscular_mycorrhizal_uptake.ammonium
        + ectomycorrhizal_uptake.ammonium,
        nitrate_change=bacterial_uptake.nitrate
        + saprotrophic_fungal_uptake.nitrate
        + arbuscular_mycorrhizal_uptake.nitrate
        + ectomycorrhizal_uptake.nitrate,
        dop_uptake=(
            bacterial_uptake.organic_phosphorus
            + saprotrophic_fungal_uptake.organic_phosphorus
            + arbuscular_mycorrhizal_uptake.organic_phosphorus
            + ectomycorrhizal_uptake.organic_phosphorus
        ),
        labile_p_change=(
            bacterial_uptake.inorganic_phosphorus
            + saprotrophic_fungal_uptake.inorganic_phosphorus
            + arbuscular_mycorrhizal_uptake.inorganic_phosphorus
            + ectomycorrhizal_uptake.inorganic_phosphorus
        ),
        bacteria_change=bacterial_growth - biomass_losses.bacteria,
        saprotrophic_fungi_change=saprotrophic_fungal_growth
        - biomass_losses.saprotrophic_fungi,
        arbuscular_mycorrhiza_change=arbuscular_mycorrhizal_growth
        - biomass_losses.arbuscular_mycorrhiza,
        ectomycorrhiza_change=ectomycorrhizal_growth - biomass_losses.ectomycorrhiza,
        pom_enzyme_bacteria_change=enzyme_changes.net_change_pom_bacteria,
        maom_enzyme_bacteria_change=enzyme_changes.net_change_maom_bacteria,
        pom_enzyme_fungi_change=enzyme_changes.net_change_pom_fungi,
        maom_enzyme_fungi_change=enzyme_changes.net_change_maom_fungi,
        necromass_generation=(
            enzyme_changes.denaturation_pom_bacteria
            + enzyme_changes.denaturation_maom_bacteria
            + enzyme_changes.denaturation_pom_fungi
            + enzyme_changes.denaturation_maom_fungi
            + biomass_losses.bacteria
            + biomass_losses.saprotrophic_fungi
            + biomass_losses.arbuscular_mycorrhiza
            + biomass_losses.ectomycorrhiza
        ),
        necromass_n_flow=necromass_n_flow,
        necromass_p_flow=necromass_p_flow,
        fruiting_body_production=fungal_fruiting_body_production,
    )


def calculate_biomass_losses(
    pools: PoolData,
    microbial_groups: dict[str, MicrobialGroupConstants],
    soil_temp: NDArray[np.floating],
) -> BiomassLosses:
    """Calculate the rate of biomass loss for each microbial group.

    Args:
        pools: Data class containing the various soil pools.
        microbial_groups: Set of microbial functional groups defined in the soil model.
        soil_temp: temperature of the microbially active soil [degrees C]

    Returns:
        The rate of biomass loss of each microbial functional group [kg C m^-3 day^-1]
    """

    return BiomassLosses(
        **{
            group.name: calculate_maintenance_biomass_synthesis(
                microbe_pool_size=getattr(pools, f"soil_c_pool_{group.name}"),
                soil_temp=soil_temp,
                microbial_group=group,
            )
            for group in microbial_groups.values()
        }
    )


def calculate_enzyme_mediated_rates(
    pools: PoolData,
    soil_temp: NDArray[np.floating],
    env_factors: EnvironmentalEffectFactors,
    enzyme_classes: dict[str, SoilEnzymeClass],
) -> EnzymeMediatedRates:
    """Calculate the rates of each enzyme mediated reaction.

    Args:
        pools: Data class containing the various soil pools.
        soil_temp: soil temperature for each soil grid cell [degrees C]
        env_factors: Data class containing the various factors through which the
            environment effects soil cycling rates.
        enzyme_classes: Details of the enzyme classes used in the soil model.

    Returns:
        A dataclass containing the enzyme mediated decomposition rates of both the
        :term:`POM` and :term:`MAOM` pool.
    """

    substrates = ["pom", "maom"]
    sources = ["bacteria", "fungi"]

    decomposition_rates = {
        f"{substrate}_to_lmwc": np.sum(
            [
                calculate_enzyme_mediated_decomposition(
                    soil_c_pool=getattr(pools, f"soil_c_pool_{substrate}"),
                    soil_enzyme=getattr(pools, f"soil_enzyme_{substrate}_{source}"),
                    soil_temp=soil_temp,
                    env_factors=env_factors,
                    enzyme_class=enzyme_classes[f"{source}_{substrate}"],
                )
                for source in sources
            ],
            axis=0,
        )
        for substrate in substrates
    }

    return EnzymeMediatedRates(**decomposition_rates)


def calculate_nutrient_removal_by_water(
    soil_c_pool_lmwc: NDArray[np.floating],
    soil_n_pool_don: NDArray[np.floating],
    soil_p_pool_dop: NDArray[np.floating],
    soil_n_pool_ammonium: NDArray[np.floating],
    soil_n_pool_nitrate: NDArray[np.floating],
    soil_p_pool_labile: NDArray[np.floating],
    vertical_flow_rates: NDArray[np.floating],
    soil_moisture: NDArray[np.floating],
    layer_structure: LayerStructure,
    constants: SoilConstants,
) -> WaterRemovalRates:
    """Calculate the rate a which each soluble nutrient pool is removed by water.

    Removal rates are calculated for the low molecular weight carbon pool and the
    inorganic nitrogen and phosphorus pools based on their solubility and the rate at
    which water exits the microbially active part of the soil. The removal rates for
    organic nitrogen and phosphorus are then calculated based on the stoichiometry and
    removal rate of the LMWC pool.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_n_pool_don: Dissolved organic nitrogen pool [kg N m^-3]
        soil_p_pool_dop: Dissolved organic phosphorus pool [kg P m^-3]
        soil_n_pool_ammonium: Soil ammonium pool [kg N m^-3]
        soil_n_pool_nitrate: Soil nitrate pool [kg N m^-3]
        soil_p_pool_labile: Labile inorganic phosphorus pool [kg P m^-3]
        vertical_flow_rates: Rates of flow downwards between the different soil layers
            [mm day^-1]
        soil_moisture: Volume of water contained in topsoil layer [mm]
        layer_structure: The details of the layer structure used across the Virtual
                Ecosystem.
        constants: Set of constants for the soil model.

    Returns:
        A dataclass containing the rate a which each soluble nutrient pool is removed by
        flows of water through the soil.
    """

    total_exit_rate = find_water_outflow_rates(
        vertical_flow=vertical_flow_rates, layer_structure=layer_structure
    )

    # Find rates at which water removes soluble nutrients
    labile_carbon_removal = calculate_solute_removal_by_soil_water(
        solute_density=soil_c_pool_lmwc,
        exit_rate=total_exit_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_lmwc,
    )
    ammonium_removal = calculate_solute_removal_by_soil_water(
        solute_density=soil_n_pool_ammonium,
        exit_rate=total_exit_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_ammonium,
    )
    nitrate_removal = calculate_solute_removal_by_soil_water(
        solute_density=soil_n_pool_nitrate,
        exit_rate=total_exit_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_nitrate,
    )
    labile_phosphorus_removal = calculate_solute_removal_by_soil_water(
        solute_density=soil_p_pool_labile,
        exit_rate=total_exit_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_labile_p,
    )

    # Find rate at which don and dop are lost due to lmwc removal
    c_n_ratio_lmwc = soil_c_pool_lmwc / soil_n_pool_don
    c_p_ratio_lmwc = soil_c_pool_lmwc / soil_p_pool_dop
    don_removal = labile_carbon_removal / c_n_ratio_lmwc
    dop_removal = labile_carbon_removal / c_p_ratio_lmwc

    return WaterRemovalRates(
        lmwc=labile_carbon_removal,
        don=don_removal,
        dop=dop_removal,
        ammonium=np.where(ammonium_removal >= 0.0, ammonium_removal, 0.0),
        nitrate=np.where(nitrate_removal >= 0.0, nitrate_removal, 0.0),
        labile_P=np.where(
            labile_phosphorus_removal >= 0.0, labile_phosphorus_removal, 0.0
        ),
    )


def calculate_enzyme_changes(
    pools: PoolData,
    enzyme_production: dict[str, NDArray[np.floating]],
    enzyme_classes: dict[str, SoilEnzymeClass],
) -> EnzymePoolChanges:
    """Calculate the change in each of the soil enzyme pools.

    Args:
        pools: Data class containing the various soil pools.
        enzyme_production: Production rates for each class of enzyme [kg C m^-3 day^-1]
        constants: Set of constants for the soil model.
        enzyme_classes: Details of the enzyme classes used in the soil model.

    Returns:
        A dataclass containing the net changes in each enzyme class, as well as the
        combined denaturation rates of the bacterial and fungal enzyme classes.
    """

    substrates = ["pom", "maom"]
    sources = ["bacteria", "fungi"]

    enzyme_changes = {
        source: {
            substrate: {
                key: value
                for key, value in zip(
                    ["net_change", "denaturation"],
                    calculate_net_enzyme_change(
                        enzyme_pool_size=getattr(
                            pools, f"soil_enzyme_{substrate}_{source}"
                        ),
                        enzyme_production=enzyme_production[f"{source}_{substrate}"],
                        enzyme_turnover_rate=enzyme_classes[
                            f"{source}_{substrate}"
                        ].turnover_rate,
                    ),
                )
            }
            for substrate in substrates
        }
        for source in sources
    }

    return EnzymePoolChanges(
        net_change_pom_bacteria=enzyme_changes["bacteria"]["pom"]["net_change"],
        net_change_maom_bacteria=enzyme_changes["bacteria"]["maom"]["net_change"],
        net_change_pom_fungi=enzyme_changes["fungi"]["pom"]["net_change"],
        net_change_maom_fungi=enzyme_changes["fungi"]["maom"]["net_change"],
        denaturation_pom_bacteria=enzyme_changes["bacteria"]["pom"]["denaturation"],
        denaturation_maom_bacteria=enzyme_changes["bacteria"]["maom"]["denaturation"],
        denaturation_pom_fungi=enzyme_changes["fungi"]["pom"]["denaturation"],
        denaturation_maom_fungi=enzyme_changes["fungi"]["maom"]["denaturation"],
    )


def calculate_net_enzyme_change(
    enzyme_pool_size: NDArray[np.floating],
    enzyme_production: NDArray[np.floating],
    enzyme_turnover_rate: float,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Calculate the change in concentration for a specific enzyme pool.

    Enzyme production rates are assumed to scale linearly with the total biomass loss
    rate of the microbes. These are combined with turnover rates to find the net change
    in the enzyme pool of interest.

    Args:
        enzyme_pool_size: Amount of enzyme class of interest [kg C m^-3]
        enzyme_production: Production rate for the enzyme in question [kg C m^-3 day^-1]
        enzyme_turnover_rate: Rate at which the enzyme denatures [day^-1]

    Returns:
        A tuple containing the net rate of change in the enzyme pool, and the
        denaturation rate of the enzyme of interest.
    """

    # Calculate production and turnover of each enzyme class
    enzyme_turnover = calculate_enzyme_turnover(
        enzyme_pool=enzyme_pool_size, turnover_rate=enzyme_turnover_rate
    )

    # return net changes in the enzyme and the necromass addition
    return (enzyme_production - enzyme_turnover, enzyme_turnover)


def calculate_enzyme_production(
    microbial_groups: dict[str, MicrobialGroupConstants],
    growth_rates: dict[str, NDArray[np.floating]],
) -> dict[str, NDArray[np.floating]]:
    """Calculate the total production of each enzyme class.

    This function checks which substrates each functional group produces enzymes for,
    and then calculates the enzyme productions based on the growth rates and the
    proportional enzyme production.

    Args:
        microbial_groups: Set of microbial functional groups defined in the soil model
        growth_rates: The (gross) growth rates of each microbial group [kg C m^-3
            day^-1]

    Returns:
        A dictionary containing the total production rate of each enzyme class [kg C
        m^-3 day^-1]
    """

    production_rates: dict[str, NDArray[np.floating]] = {}

    for group in microbial_groups.values():
        for substrate in group.find_enzyme_substrates():
            enzyme_class = f"{group.taxonomic_group}_{substrate}"

            # This step catches negative growth rates (which can occur for mycorrhizal
            # fungi, but shouldn't produce a negative amount of enzyme)
            growth = np.where(growth_rates[group.name] > 0, growth_rates[group.name], 0)

            if enzyme_class in production_rates.keys():
                production_rates[enzyme_class] += (
                    growth * group.enzyme_production[substrate]
                )
            else:
                production_rates[enzyme_class] = (
                    growth * group.enzyme_production[substrate]
                )

    return production_rates


def calculate_fruiting_body_production(
    microbial_groups: dict[str, MicrobialGroupConstants],
    growth_rates: dict[str, NDArray[np.floating]],
) -> NDArray[np.floating]:
    """Calculate the total production of fungal fruiting bodies by all microbial groups.

    Args:
        microbial_groups: Set of microbial functional groups defined in the soil model
        growth_rates: The (gross) growth rates of each microbial group [kg C m^-3
            day^-1]

    Returns:
        The total production rate of fungal fruiting bodies by the soil microbes [kg C
        m^-3 day^-1]
    """

    fruiting_body_production = np.zeros_like(growth_rates["bacteria"])

    for group in microbial_groups.values():
        # Only fungi produce fruiting bodies so only add contributions from them
        if group.taxonomic_group == "fungi":
            # This step catches negative growth rates (which can occur for mycorrhizal
            # fungi, but shouldn't produce a negative amount of fruiting bodies)
            growth = np.where(growth_rates[group.name] > 0, growth_rates[group.name], 0)

            fruiting_body_production += growth * group.reproductive_allocation

    return fruiting_body_production


def calculate_maintenance_biomass_synthesis(
    microbe_pool_size: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    microbial_group: MicrobialGroupConstants,
) -> NDArray[np.floating]:
    """Calculate biomass synthesis rate required to offset losses for a microbial pool.

    In order for a microbial population to not decline it must synthesise enough new
    biomass to offset losses. These losses mostly come from cell death and protein
    decay, but also include loses due to extracellular enzyme excretion.

    Args:
        microbe_pool_size: Size of the microbial pool of interest [kg C m^-3]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        microbial_group: Constants associated with the microbial group of interest

    Returns:
        The rate of microbial biomass loss that must be matched to maintain a steady
        population [kg C m^-3 day^-1]
    """

    temp_factor = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=microbial_group.activation_energy_turnover,
        reference_temperature=microbial_group.reference_temperature,
    )

    return microbial_group.turnover_rate * temp_factor * microbe_pool_size


def calculate_enzyme_turnover(
    enzyme_pool: NDArray[np.floating], turnover_rate: float
) -> NDArray[np.floating]:
    """Calculate the turnover rate of a specific enzyme class.

    Args:
        enzyme_pool: The pool size for the enzyme class in question [kg C m^-3]
        turnover_rate: The rate at which enzymes in the pool turnover [day^-1]

    Returns:
        The rate at which enzymes are lost from the pool [kg C m^-3 day^-1]
    """

    return turnover_rate * enzyme_pool


def calculate_enzyme_mediated_decomposition(
    soil_c_pool: NDArray[np.floating],
    soil_enzyme: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    env_factors: EnvironmentalEffectFactors,
    enzyme_class: SoilEnzymeClass,
) -> NDArray[np.floating]:
    """Calculate rate of a enzyme mediated decomposition process.

    This function calculates various environmental factors that effect enzyme activity,
    then uses these to find environmental adjusted rate and saturation constants. These
    are then used to find the decomposition rate of the pool in question.

    Args:
        soil_c_pool: Size of organic matter pool [kg C m^-3]
        soil_enzyme: Amount of enzyme class which breaks down the organic matter pool in
            question [kg C m^-3]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        env_factors: Data class containing the various factors through which the
            environment effects soil cycling rates.
        enzyme_class: Constants associated with the enzyme class in question.

    Returns:
        The rate of decomposition of the organic matter pool in question [kg C m^-3
        day^-1]
    """

    # Calculate the factors which impact the rate and saturation constants
    temp_factor_rate = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=enzyme_class.activation_energy_rate,
        reference_temperature=enzyme_class.reference_temperature,
    )
    temp_factor_saturation = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=enzyme_class.activation_energy_saturation,
        reference_temperature=enzyme_class.reference_temperature,
    )

    # Calculate the adjusted rate and saturation constants
    rate_constant = (
        enzyme_class.maximum_rate
        * temp_factor_rate
        * env_factors.water
        * env_factors.pH
    )
    saturation_constant = (
        enzyme_class.half_saturation_constant
        * temp_factor_saturation
        * env_factors.clay_saturation
    )

    return (
        rate_constant * soil_enzyme * soil_c_pool / (saturation_constant + soil_c_pool)
    )


def calculate_maom_desorption(
    soil_c_pool_maom: NDArray[np.floating], desorption_rate_constant: float
):
    """Calculate the rate of mineral associated organic matter (MAOM) desorption.

    This function is independent of soil temperature, moisture, pH, clay fraction and
    bulk density. All of these things are known to effect real world desorption rates.
    However, to simplify the parameterisation we only include these effects on microbial
    rates. This may be something we want to alter in future.

    Args:
        soil_c_pool_maom: Size of the mineral associated organic matter pool [kg C m^-3]
        desorption_rate_constant: Rate constant for MAOM desorption [day^-1]

    Returns:
        The rate of MAOM desorption to LMWC [kg C m^-3 day^-1]
    """

    return desorption_rate_constant * soil_c_pool_maom


def calculate_sorption_to_maom(
    soil_c_pool: NDArray[np.floating], sorption_rate_constant: float
):
    """Calculate that a carbon pool sorbs to become mineral associated organic matter.

    Carbon from both the low molecular weight carbon pool and the necromass pool can
    sorb to minerals to form MAOM, so this function can be used for either pool.

    This function is independent of soil temperature, moisture, pH, clay fraction and
    bulk density. All of these things are known to effect real world desorption rates.
    However, to simplify the parameterisation we only include these effects on microbial
    rates. This may be something we want to alter in future.

    Args:
        soil_c_pool: Size of carbon pool [kg C m^-3]
        sorption_rate_constant: Rate constant for sorption to MAOM [day^-1]

    Returns:
        The rate of sorption to MAOM [kg C m^-3 day^-1]
    """

    return sorption_rate_constant * soil_c_pool


def calculate_necromass_breakdown(
    soil_c_pool_necromass: NDArray[np.floating], necromass_decay_rate: float
) -> NDArray[np.floating]:
    """Calculate breakdown rate of necromass into low molecular weight carbon (LMWC).

    This function calculate necromass breakdown to LMWC as a simple exponential decay.
    This decay is not effected by temperature or any other environmental factor. The
    idea is to keep this function as simple as possible, because it will be hard to
    parametrise even without additional complications. However, this is a simplification
    to bear in mind when planning future model improvements.

    Args:
        soil_c_pool_necromass: Size of the microbial necromass pool [kg C m^-3]
        necromass_decay_rate: Rate at which necromass decays into LMWC [day^-1]

    Returns:
        The amount of necromass that breakdown to LMWC [kg C m^-3 day^-1]
    """

    return necromass_decay_rate * soil_c_pool_necromass


def calculate_litter_mineralisation_fluxes(
    litter_C_mineralisation_rate: NDArray[np.floating],
    litter_N_mineralisation_rate: NDArray[np.floating],
    litter_P_mineralisation_rate: NDArray[np.floating],
    constants: SoilConstants,
) -> LitterMineralisationFluxes:
    """Calculate the split of the litter mineralisation fluxes between soil pools.

    Each mineralisation flux from litter to soil has to be split between the particulate
    and dissolved pools for the nutrient in question. The leached nitrogen and
    phosphorus fluxes are further split between organic and inorganic forms, with the
    inorganic leached nitrogen assumed to be entirely in the form of ammonium.

    Args:
        litter_C_mineralisation_rate: The rate at which carbon is being mineralised from
            the litter [kg C m^-3 day^-1]
        litter_N_mineralisation_rate: The rate at which nitrogen is being mineralised
            from the litter [kg N m^-3 day^-1]
        litter_P_mineralisation_rate: The rate at which phosphorus is being mineralised
            from the litter [kg P m^-3 day^-1]
        constants: Set of constants for the soil model.

    Returns:
        A dataclass containing the flux into each pool due to litter mineralisation [kg
        nutrient m^-3 day^-1].
    """

    flux_C_particulate, flux_C_dissolved = calculate_litter_mineralisation_split(
        mineralisation_rate=litter_C_mineralisation_rate,
        litter_leaching_coefficient=constants.litter_leaching_fraction_carbon,
    )
    flux_N_particulate, flux_N_dissolved = calculate_litter_mineralisation_split(
        mineralisation_rate=litter_N_mineralisation_rate,
        litter_leaching_coefficient=constants.litter_leaching_fraction_nitrogen,
    )
    flux_N_organic_dissolved = (
        flux_N_dissolved * constants.organic_proportion_litter_nitrogen_leaching
    )
    flux_N_inorganic_dissolved = flux_N_dissolved * (
        1 - constants.organic_proportion_litter_nitrogen_leaching
    )
    flux_P_particulate, flux_P_dissolved = calculate_litter_mineralisation_split(
        mineralisation_rate=litter_P_mineralisation_rate,
        litter_leaching_coefficient=constants.litter_leaching_fraction_phosphorus,
    )
    flux_P_organic_dissolved = (
        flux_P_dissolved * constants.organic_proportion_litter_phosphorus_leaching
    )
    flux_P_inorganic_dissolved = flux_P_dissolved * (
        1 - constants.organic_proportion_litter_phosphorus_leaching
    )

    return LitterMineralisationFluxes(
        lmwc=flux_C_dissolved,
        pom=flux_C_particulate,
        don=flux_N_organic_dissolved,
        ammonium=flux_N_inorganic_dissolved,
        particulate_n=flux_N_particulate,
        dop=flux_P_organic_dissolved,
        labile_p=flux_P_inorganic_dissolved,
        particulate_p=flux_P_particulate,
    )


def calculate_litter_mineralisation_split(
    mineralisation_rate: NDArray[np.floating], litter_leaching_coefficient: float
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Determine how nutrients from litter mineralisation get split between soil pools.

    All nutrients that we track (carbon, nitrogen and phosphorus) get divided between
    the particulate organic matter pool and the dissolved pool for their respective
    nutrient (for the carbon case this pool is termed low molecular weight carbon). This
    split is calculated based on empirically derived litter leaching constants.

    Args:
        mineralisation_rate: The rate at which the nutrient is being mineralised from
            the litter [kg C m^-3 day^-1]
        litter_leaching_coefficient: Fraction of the litter mineralisation of the
            nutrient that occurs via leaching rather than as particulates [unitless]

    Returns:
        The rate at which the nutrient is added to the soil as particulates (first part
        of tuple) and as dissolved matter (second part of tuple) [kg nutrient m^-3
        day^-1].
    """

    return (
        (1 - litter_leaching_coefficient) * mineralisation_rate,
        litter_leaching_coefficient * mineralisation_rate,
    )


def calculate_soil_nutrient_mineralisation(
    pool_carbon: NDArray[np.floating],
    pool_nutrient: NDArray[np.floating],
    breakdown_rate: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Calculate mineralisation rate from soil organic matter for a specific nutrient.

    This function assumes that nutrients are mineralised in direct proportion to their
    ratio to carbon in the decaying organic matter. This function is therefore does not
    capture mechanisms that exist to actively release nutrients from organic matter
    (e.g. phosphatase enzymes).

    Args:
        pool_carbon: The carbon content of the organic matter pool [kg C m^-3]
        pool_nutrient: The nutrient content of the organic matter pool [kg nutrient
            m^-3]
        breakdown_rate: The rate at which the pool is being broken down (expressed in
            carbon terms) [kg C m^-3 day^-1]

    Returns:
        The rate at which the nutrient in question is mineralised due to organic matter
        breakdown [kg nutrient m^-3 day^-1]
    """

    carbon_nutrient_ratio = pool_carbon / pool_nutrient
    return breakdown_rate / carbon_nutrient_ratio


def calculate_nutrient_flows_to_necromass(
    biomass_losses: BiomassLosses,
    enzyme_changes: EnzymePoolChanges,
    microbial_groups: dict[str, MicrobialGroupConstants],
    enzyme_classes: dict[str, SoilEnzymeClass],
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Calculate the rate at which nutrients flow into the necromass pool.

    These flows comprise of the nitrogen and phosphorus content of the dead cells and
    denatured enzymes that flow into the necromass pool.

    Args:
        biomass_losses: Rate at which biomass of each microbial functional group becomes
            necromass [kg C m^-3 day^-1]
        enzyme_changes: Details of the rate change for the soil enzyme pools.
        microbial_groups: Set of microbial functional groups defined in the soil model
        enzyme_classes: Details of the enzyme classes used by the soil model.

    Returns:
        A tuple containing the rates at which nitrogen [kg N m^-3 day^-1] and phosphorus
        [kg P m^-3 day^-1] are added to the soil necromass pool
    """

    # Calculate nutrient flows due to cellular losses
    necromass_n_cellular = sum(
        getattr(biomass_losses, group) / microbial_groups[group].c_n_ratio
        for group in microbial_groups.keys()
    )
    necromass_p_cellular = sum(
        getattr(biomass_losses, group) / microbial_groups[group].c_p_ratio
        for group in microbial_groups.keys()
    )
    # And those due to enzyme denaturation
    necromass_n_enzyme = sum(
        getattr(enzyme_changes, f"denaturation_{substrate}_{group}")
        / enzyme_classes[f"{group}_{substrate}"].c_n_ratio
        for group in ["bacteria", "fungi"]
        for substrate in ["maom", "pom"]
    )
    necromass_p_enzyme = sum(
        getattr(enzyme_changes, f"denaturation_{substrate}_{group}")
        / enzyme_classes[f"{group}_{substrate}"].c_p_ratio
        for group in ["bacteria", "fungi"]
        for substrate in ["maom", "pom"]
    )

    return (
        necromass_n_cellular + necromass_n_enzyme,
        necromass_p_cellular + necromass_p_enzyme,
    )


def find_necromass_nutrient_outflows(
    necromass_carbon: NDArray[np.floating],
    necromass_nitrogen: NDArray[np.floating],
    necromass_phosphorus: NDArray[np.floating],
    necromass_decay: NDArray[np.floating],
    necromass_sorption: NDArray[np.floating],
) -> dict[str, NDArray[np.floating]]:
    """Find the amount of each nutrient flowing out of the necromass pool.

    There are two sources for this outflow. Firstly, the decay of necromass to dissolved
    organic nitrogen/phosphorus. Secondly, the sorption of necromass to soil minerals to
    form mineral associated organic matter. A key assumption here is that the nitrogen
    and phosphorus flows directly follows the carbon flow, i.e. it follows the same
    split between pathways as the carbon does.

    Args:
        necromass_carbon: The amount of carbon stored as microbial necromass [kg C m^-3]
        necromass_nitrogen: The amount of nitrogen stored as microbial necromass [kg N
            m^-3]
        necromass_phosphorus: The amount of phosphorus stored as microbial necromass [kg
            P m^-3]
        necromass_decay: The rate at which necromass decays to form lmwc [kg C m^-3
            day^-1]
        necromass_sorption: The rate at which necromass gets sorbed to soil minerals to
            form mineral associated organic matter [kg C m^-3 day^-1]

    Returns:
        A dictionary containing the rates at which nitrogen and phosphorus contained in
        necromass is released as dissolved organic nitrogen, and the rates at which they
        gets sorbed to soil minerals to form soil associated organic matter [kg nutrient
        m^-3 day^-1].
    """

    # Find carbon:nitrogen and carbon:phosphorus ratios of the necromass
    c_n_ratio = necromass_carbon / necromass_nitrogen
    c_p_ratio = necromass_carbon / necromass_phosphorus

    return {
        "decay_nitrogen": necromass_decay / c_n_ratio,
        "sorption_nitrogen": necromass_sorption / c_n_ratio,
        "decay_phosphorus": necromass_decay / c_p_ratio,
        "sorption_phosphorus": necromass_sorption / c_p_ratio,
    }


def calculate_net_nutrient_transfers_from_maom_to_lmwc(
    lmwc_carbon: NDArray[np.floating],
    lmwc_nitrogen: NDArray[np.floating],
    lmwc_phosphorus: NDArray[np.floating],
    maom_carbon: NDArray[np.floating],
    maom_nitrogen: NDArray[np.floating],
    maom_phosphorus: NDArray[np.floating],
    maom_breakdown: NDArray[np.floating],
    maom_desorption: NDArray[np.floating],
    lmwc_sorption: NDArray[np.floating],
) -> dict[str, NDArray[np.floating]]:
    """Calculate the net rate of transfer of nutrients between MAOM and LMWC.

    Args:
        lmwc_carbon: The amount of carbon stored as low molecular weight carbon [kg C
            m^-3]
        lmwc_nitrogen: The amount of nitrogen stored as low molecular weight
            carbon/dissolved organic nitrogen [kg N m^-3]
        lmwc_phosphorus: The amount of phosphorus stored as low molecular weight
            carbon/dissolved organic phosphorus [kg P m^-3]
        maom_carbon: The amount of carbon stored as mineral associated organic matter
            [kg C m^-3]
        maom_nitrogen: The amount of nitrogen stored as mineral associated organic
            matter [kg N m^-3]
        maom_phosphorus: The amount of phosphorus stored as mineral associated organic
            matter [kg P m^-3]
        maom_breakdown: The rate at which the mineral associated organic matter pool is
            being broken down by enzymes (expressed in carbon terms) [kg C m^-3 day^-1]
        maom_desorption: The rate at which the mineral associated organic matter pool is
            spontaneously desorbing [kg C m^-3 day^-1]
        lmwc_sorption: The rate at which the low molecular weight carbon pool is sorbing
            to minerals to form mineral associated organic matter [kg C m^-3 day^-1]

    Returns:
        The net nutrient transfer rates of transfer from mineral associated organic
        matter into dissolved organic forms. This is currently includes nitrogen and
        phosphorus [kg nutrient m^-3 day^-1]
    """

    # Find carbon:nitrogen ratio of the lwmc and maom
    c_n_ratio_lmwc = lmwc_carbon / lmwc_nitrogen
    c_n_ratio_maom = maom_carbon / maom_nitrogen

    maom_nitrogen_gain = lmwc_sorption / c_n_ratio_lmwc
    maom_nitrogen_loss = (maom_breakdown + maom_desorption) / c_n_ratio_maom

    # Find carbon:phosphorus ratio of the lwmc and maom
    c_p_ratio_lmwc = lmwc_carbon / lmwc_phosphorus
    c_p_ratio_maom = maom_carbon / maom_phosphorus

    maom_phosphorus_gain = lmwc_sorption / c_p_ratio_lmwc
    maom_phosphorus_loss = (maom_breakdown + maom_desorption) / c_p_ratio_maom

    return {
        "nitrogen": maom_nitrogen_loss - maom_nitrogen_gain,
        "phosphorus": maom_phosphorus_loss - maom_phosphorus_gain,
    }


def calculate_rate_of_nitrification(
    soil_temp: NDArray[np.floating],
    effective_saturation: NDArray[np.floating],
    soil_n_pool_ammonium: NDArray[np.floating],
    constants: SoilConstants,
) -> NDArray[np.floating]:
    """Calculate the rate at which ammonium nitrifies to form nitrate.

    This is an empirical relationship that we have taken from
    :cite:t:`fatichi_mechanistic_2019`.

    Args:
        soil_temp: Temperature of the relevant segment of soil [C]
        effective_saturation: Effective saturation of the soil with water [unitless]
        soil_n_pool_ammonium: Soil ammonium pool [kg N m^-3]
        constants: Set of constants for the soil model.

    Returns:
        The rate at which ammonium nitrifies to form nitrate [kg N m^-3 day^-1].
    """

    # Calculate moisture and temperature factors
    temp_factor = calculate_nitrification_temperature_factor(
        soil_temp=soil_temp,
        optimum_temp=constants.nitrification_optimum_temperature,
        max_temp=constants.nitrification_maximum_temperature,
        thermal_sensitivity=constants.nitrification_thermal_sensitivity,
    )
    moisture_factor = calculate_nitrification_moisture_factor(
        effective_saturation=effective_saturation
    )

    return np.where(
        soil_n_pool_ammonium >= 0.0,
        constants.nitrification_rate_constant
        * temp_factor
        * moisture_factor
        * soil_n_pool_ammonium,
        0.0,
    )


def calculate_rate_of_denitrification(
    soil_temp: NDArray[np.floating],
    effective_saturation: NDArray[np.floating],
    soil_n_pool_nitrate: NDArray[np.floating],
    constants: SoilConstants,
) -> NDArray[np.floating]:
    """Calculate the rate at which nitrate denitrifies (and leaves the soil).

    This is an empirical relationship that we have taken from
    :cite:t:`fatichi_mechanistic_2019`.

    Args:
        soil_temp: Temperature of the relevant segment of soil [C]
        effective_saturation: Effective saturation of the soil with water [unitless]
        soil_n_pool_nitrate: Soil nitrate pool [kg N m^-3]
        constants: Set of constants for the soil model.

    Returns:
        The rate at which ammonium nitrifies to form nitrate [kg N m^-3 day^-1].
    """

    # Calculate moisture and temperature factors
    temp_factor = calculate_denitrification_temperature_factor(
        soil_temp=soil_temp,
        factor_at_infinity=constants.denitrification_infinite_temperature_factor,
        minimum_temp=constants.denitrification_minimum_temperature,
        thermal_sensitivity=constants.denitrification_thermal_sensitivity,
    )
    moisture_factor = effective_saturation**2

    return np.where(
        soil_n_pool_nitrate >= 0.0,
        constants.denitrification_rate_constant
        * temp_factor
        * moisture_factor
        * soil_n_pool_nitrate,
        0.0,
    )


def calculate_symbiotic_nitrogen_fixation(
    carbon_supply: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    constants: SoilConstants,
) -> NDArray[np.floating]:
    """Calculate rate of nitrogen fixation by plant symbionts.

    The nitrogen is considered to be fixed solely in the form of ammonium.

    Args:
        carbon_supply: The rate at which carbon is supplied to symbiotic partners by
            plants for the purpose of nitrogen fixation [kg C m^-3 day^-1]
        soil_temp: Temperature of the relevant soil zone [C]
        constants: Set of constants for the soil model.

    Returns:
        The rate at which nitrogen is fixed by plant associated microbial symbionts [kg
        N m^-3 day^-1]
    """

    fixation_carbon_cost = calculate_symbiotic_nitrogen_fixation_carbon_cost(
        soil_temp=soil_temp,
        cost_at_zero_celsius=constants.nitrogen_fixation_cost_zero_celcius,
        infinite_temp_cost_offset=constants.nitrogen_fixation_cost_infinite_temp_offset,
        thermal_sensitivity=constants.nitrogen_fixation_cost_thermal_sensitivity,
        cost_equality_temp=constants.nitrogen_fixation_cost_equality_temperature,
    )

    return carbon_supply / fixation_carbon_cost


def calculate_free_living_nitrogen_fixation(
    soil_temp: NDArray[np.floating],
    fixation_at_reference: float,
    reference_temperature: float,
    q10_nitrogen_fixation: float,
    active_depth: float,
) -> NDArray[np.floating]:
    """Calculate rate of nitrogen fixation by free living microbes.

    These are microbes not in a symbiotic association with plants. They are considered
    to fix nitrogen solely in the form of ammonium. The functional form used is taken
    from :cite:t:`lin_modelling_2000`.

    TODO: At the moment this function takes in soil temperatures in Celsius and
    converts them to Kelvin, this should be reviewed as part of the soil-abiotic links
    review.

    Args:
        soil_temp: Temperature of the relevant soil zone [C]
        fixation_at_reference: Rate of nitrogen fixation at the reference temperature
            [kg N m^-2 day^-1]
        reference_temperature: Reference temperature [K]
        q10_nitrogen_fixation: Q10 temperature coefficient for free-living nitrogen
            fixation [unitless]
        active_depth: The depth to which the soil is considered to be biologically
            active [m]

    Returns:
        The rate at which nitrogen is fixed by free living (i.e. non-symbiotic) microbes
        [kg N m^-3 day^-1]
    """

    soil_temp_in_kelvin = convert_temperature(
        soil_temp, old_scale="Celsius", new_scale="Kelvin"
    )

    # Convert the fixation rate from per area to per volume units based on the active
    # soil depth
    fixation_at_reference_volume = fixation_at_reference / active_depth

    return fixation_at_reference_volume * q10_nitrogen_fixation ** (
        (soil_temp_in_kelvin - reference_temperature) / 10.0
    )


def calculate_net_formation_of_secondary_P(
    soil_p_pool_labile: NDArray[np.floating],
    soil_p_pool_secondary: NDArray[np.floating],
    secondary_p_breakdown_rate: float,
    labile_p_sorption_rate: float,
) -> NDArray[np.floating]:
    """Calculate net rate of secondary mineral phosphorus formation.

    This is the combination of labile inorganic phosphorus associating with minerals and
    secondary mineral phosphorus breaking down.

    Args:
        soil_p_pool_labile: Labile inorganic phosphorus pool [kg P m^-3]
        soil_p_pool_secondary: Secondary mineral phosphorus pool [kg P m^-3]
        secondary_p_breakdown_rate: Rate constant for breakdown of secondary mineral
            phosphorus to labile phosphorus [day^-1]
        labile_p_sorption_rate: Rate constant for sorption of labile inorganic
            phosphorus to soil minerals to form secondary mineral phosphorus [day^-1]

    Returns:
        The net rate of labile inorganic phosphorus that has become secondary mineral
        phosphorus (this can be negative) [kg P m^-3 day^-1]
    """

    association_rate = np.where(
        soil_p_pool_labile >= 0.0, labile_p_sorption_rate * soil_p_pool_labile, 0.0
    )
    breakdown_rate = secondary_p_breakdown_rate * soil_p_pool_secondary

    return association_rate - breakdown_rate


def calculate_fungal_fruiting_body_decay(
    decay_rate: NDArray[np.floating],
    fungal_fruiting_body_c_n_ratio: float,
    fungal_fruiting_body_c_p_ratio: float,
) -> dict[str, NDArray[np.floating]]:
    """Calculate contribution to different soil pools from fungal fruiting body decay.

    Fungal fruiting bodies are organic matter so they decay into three soil pools:
    :term:`LMWC`, :term:`DON` and :term:`DOP`. The decay rate is already known in carbon
    terms and the decay into the organic nitrogen and phosphorus pools is found based on
    this and the fixed stoichiometric ratios of the fungal fruiting bodies pool.

    Args:
        decay_rate: The rate at which fungal fruiting bodies decay in carbon terms [kg C
            m^-3 day^-1]
        fungal_fruiting_body_c_n_ratio: The carbon to nitrogen ratio of fungal fruiting
            bodies pool [unitless]
        fungal_fruiting_body_c_p_ratio: The carbon to phosphorus ratio of fungal
            fruiting bodies pool [unitless]

    Returns:
        The input rate to each soil organic matter pool (carbon, nitrogen, phosphorus)
        due to the decay of fungal fruiting bodies [kg m^-3 day^-1].
    """

    return {
        "carbon": decay_rate,
        "nitrogen": decay_rate / fungal_fruiting_body_c_n_ratio,
        "phosphorus": decay_rate / fungal_fruiting_body_c_p_ratio,
    }
