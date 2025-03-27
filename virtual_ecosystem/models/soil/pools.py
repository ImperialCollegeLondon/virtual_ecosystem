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
from virtual_ecosystem.models.litter.env_factors import (
    average_temperature_over_microbially_active_layers,
    average_water_potential_over_microbially_active_layers,
)
from virtual_ecosystem.models.soil.constants import SoilConsts
from virtual_ecosystem.models.soil.env_factors import (
    EnvironmentalEffectFactors,
    calculate_denitrification_temperature_factor,
    calculate_environmental_effect_factors,
    calculate_leaching_rate,
    calculate_nitrification_moisture_factor,
    calculate_nitrification_temperature_factor,
    calculate_symbiotic_nitrogen_fixation_carbon_cost,
    calculate_temperature_effect_on_microbes,
    find_total_soil_moisture_for_microbially_active_depth,
)
from virtual_ecosystem.models.soil.microbial_groups import (
    EnzymeConstants,
    MicrobialGroupConstants,
)


@dataclass
class MicrobialChanges:
    """Changes due to microbial uptake, biomass production and losses."""

    lmwc_uptake: NDArray[np.float32]
    """Total rate of microbial uptake of low molecular weight carbon.
    
    Units of [kg C m^-3 day^-1]."""

    don_uptake: NDArray[np.float32]
    """Total rate of microbial uptake of dissolved organic nitrogen.
    
    Units of [kg N m^-3 day^-1]."""

    ammonium_change: NDArray[np.float32]
    """Total change in the ammonium pool due to microbial activity [kg N m^-3 day^-1].
    
    This change arises from the balance of immobilisation and mineralisation of
    ammonium. A positive value indicates a net immobilisation (uptake) of ammonium."""

    nitrate_change: NDArray[np.float32]
    """Total change in the nitrate pool due to microbial activity [kg N m^-3 day^-1].

    This change arises from the balance of immobilisation and mineralisation of
    nitrate. A positive value indicates a net immobilisation (uptake) of nitrate."""

    dop_uptake: NDArray[np.float32]
    """Total rate of microbial uptake of dissolved organic phosphorus.
    
    Units of [kg P m^-3 day^-1]."""

    labile_p_change: NDArray[np.float32]
    """Total change in the labile inorganic phosphorus pool due to microbial activity.
    
    Units of [kg P m^-3 day^-1]. This change arises from the balance of immobilisation
    and mineralisation of labile P. A positive value indicates a net immobilisation
    (uptake) of P. """

    bacteria_change: NDArray[np.float32]
    """Rate of change of bacterial biomass pool [kg C m^-3 day^-1]."""

    fungi_change: NDArray[np.float32]
    """Rate of change of fungal biomass pool [kg C m^-3 day^-1]."""

    pom_enzyme_bacteria_change: NDArray[np.float32]
    """Rate of change for the bacterially produced :term:`POM` degrading enzymes.

    Units of [kg C m^-3 day^-1].
    """

    maom_enzyme_bacteria_change: NDArray[np.float32]
    """Rate of change for the bacterially produced :term:`MAOM` degrading enzymes.
    
    Units of [kg C m^-3 day^-1].
    """

    pom_enzyme_fungi_change: NDArray[np.float32]
    """Rate of change for the fungally produced :term:`POM` degrading enzymes.

    Units of [kg C m^-3 day^-1].
    """

    maom_enzyme_fungi_change: NDArray[np.float32]
    """Rate of change for the fungally produced :term:`MAOM` degrading enzymes.
    
    Units of [kg C m^-3 day^-1].
    """

    necromass_generation: NDArray[np.float32]
    """Rate at which necromass is being produced [kg C m^-3 day^-1]."""

    necromass_n_flow: NDArray[np.float32]
    """Nitrogen flow associated with necromass generation [kg N m^-3 day^-1]."""

    necromass_p_flow: NDArray[np.float32]
    """Phosphorus flow associated with necromass generation [kg P m^-3 day^-1]."""


@dataclass
class NetNutrientConsumption:
    """Net consumption of each labile due to microbial activity.

    The labile inorganic pools can have negative consumptions because microbes can
    mineralise inorganic nutrients from nutrients in organic form.
    """

    carbon: NDArray[np.float32]
    """Uptake of low molecular weight carbon [kg C m^-3 day^-1]."""

    organic_nitrogen: NDArray[np.float32]
    """Uptake of dissolved organic nitrogen [kg N m^-3 day^-1]."""

    ammonium: NDArray[np.float32]
    """Uptake of ammonium [kg N m^-3 day^-1]."""

    nitrate: NDArray[np.float32]
    """Uptake of nitrate [kg N m^-3 day^-1]."""

    organic_phosphorus: NDArray[np.float32]
    """Uptake of dissolved organic phosphorus [kg P m^-3 day^-1]."""

    inorganic_phosphorus: NDArray[np.float32]
    """Uptake of labile inorganic phosphorus [kg P m^-3 day^-1]."""


@dataclass
class EnzymeMediatedRates:
    """Rates of each enzyme mediated transfer between pools."""

    pom_to_lmwc: NDArray[np.float32]
    """Rate of particulate organic matter decomposition to low molecular weight carbon.
    
    Units of [kg C m^-3 day^-1].
    """

    maom_to_lmwc: NDArray[np.float32]
    """Rate of mineral associated organic matter decomposition to LMWC.

    Units of [kg C m^-3 day^-1].
    """


@dataclass
class EnzymePoolChanges:
    """Changes to the different enzyme pools due to production and denaturation."""

    net_change_pom_bacteria: NDArray[np.float32]
    """Net change in the bacterially produced enzyme pool that breaks down :term:`POM`.
    
    Units of [kg C m^-3 day^-1]
    """

    net_change_maom_bacteria: NDArray[np.float32]
    """Net change in the bacterially produced enzyme pool that breaks down :term:`MAOM`.
    
    Units of [kg C m^-3 day^-1]
    """

    net_change_pom_fungi: NDArray[np.float32]
    """Net change in the fungally produced enzyme pool that breaks down :term:`POM`.
    
    Units of [kg C m^-3 day^-1]
    """

    net_change_maom_fungi: NDArray[np.float32]
    """Net change in the fungally produced enzyme pool that breaks down :term:`MAOM`.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_pom_bacteria: NDArray[np.float32]
    """Denaturation rate for the :term:`POM` degrading enzyme produced by bacteria.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_maom_bacteria: NDArray[np.float32]
    """Denaturation rate for the :term:`MAOM` degrading enzyme produced by bacteria.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_pom_fungi: NDArray[np.float32]
    """Denaturation rate for the :term:`POM` degrading enzyme produced by fungi.
    
    Units of [kg C m^-3 day^-1]
    """

    denaturation_maom_fungi: NDArray[np.float32]
    """Denaturation rate for the :term:`MAOM` degrading enzyme produced by fungi.
    
    Units of [kg C m^-3 day^-1]
    """


@dataclass
class LeachingRates:
    """Leaching rate for each soluble nutrient pool."""

    lmwc: NDArray[np.float32]
    """Leaching rate for the low molecular weight carbon pool [kg C m^-3 day^-1]."""

    don: NDArray[np.float32]
    """Loss of dissolved organic nitrogen due to LMWC leaching [kg N m^-3 day^-1]."""

    dop: NDArray[np.float32]
    """Loss of dissolved organic phosphorus due to LMWC leaching [kg P m^-3 day^-1]."""

    ammonium: NDArray[np.float32]
    """Leaching rate for the soil ammonium pool [kg N m^-3 day^-1]."""

    nitrate: NDArray[np.float32]
    """Leaching rate for the soil nitrate pool [kg N m^-3 day^-1]."""

    labile_P: NDArray[np.float32]
    """Leaching rate for the labile inorganic phosphorus pool [kg P m^-3 day^-1]."""


@dataclass
class LitterMineralisationFluxes:
    """Fluxes into each soil pool due to mineralisation from litter model."""

    lmwc: NDArray[np.float32]
    """Mineralisation into the low molecular weight carbon pool [kg C m^-3 day^-1]."""

    pom: NDArray[np.float32]
    """Mineralisation into the particulate organic matter pool [kg C m^-3 day^-1]."""

    don: NDArray[np.float32]
    """Mineralisation into the dissolved organic nitrogen pool [kg N m^-3 day^-1]."""

    ammonium: NDArray[np.float32]
    """Mineralisation into the ammonium pool [kg N m^-3 day^-1]."""

    particulate_n: NDArray[np.float32]
    """Mineralisation into the particulate organic nitrogen pool [kg N m^-3 day^-1]."""

    dop: NDArray[np.float32]
    """Mineralisation into the dissolved organic phosphorus pool [kg P m^-3 day^-1]."""

    labile_p: NDArray[np.float32]
    """Mineralisation into the labile inorganic phosphorus pool [kg P m^-3 day^-1]."""

    particulate_p: NDArray[np.float32]
    """Mineralisation into the particulate organic phosphorus pool.
    
    Units of [kg P m^-3 day^-1].
    """


@dataclass
class PoolData:
    """Data class collecting the full set of soil pools updated by the soil model."""

    soil_c_pool_maom: NDArray[np.float32]
    """Mineral associated organic matter pool [kg C m^-3]."""

    soil_c_pool_lmwc: NDArray[np.float32]
    """Low molecular weight carbon pool [kg C m^-3]."""

    soil_c_pool_bacteria: NDArray[np.float32]
    """Bacterial biomass pool [kg C m^-3]."""

    soil_c_pool_fungi: NDArray[np.float32]
    """Fungal biomass pool [kg C m^-3]."""

    soil_c_pool_pom: NDArray[np.float32]
    """Particulate organic matter pool [kg C m^-3]."""

    soil_c_pool_necromass: NDArray[np.float32]
    """Microbial necromass pool [kg C m^-3]."""

    soil_enzyme_pom_bacteria: NDArray[np.float32]
    """Bacteria produced enzyme class which breaks down :term:`POM` [kg C m^-3]."""

    soil_enzyme_maom_bacteria: NDArray[np.float32]
    """Bacteria produced enzyme class which breaks down :term:`MAOM` [kg C m^-3]."""

    soil_enzyme_pom_fungi: NDArray[np.float32]
    """Fungi produced enzyme class which breaks down :term:`POM` [kg C m^-3]."""

    soil_enzyme_maom_fungi: NDArray[np.float32]
    """Fungi produced enzyme class which breaks down :term:`MAOM` [kg C m^-3]."""

    soil_n_pool_don: NDArray[np.float32]
    """Organic nitrogen content of the low molecular weight carbon pool [kg N m^-3].
    
    This also gets termed the dissolved organic nitrogen (DON) pool.
    """

    soil_n_pool_particulate: NDArray[np.float32]
    """Organic nitrogen content of the particulate organic matter pool [kg N m^-3]."""

    soil_n_pool_necromass: NDArray[np.float32]
    """Organic nitrogen content of the microbial necromass pool [kg N m^-3]."""

    soil_n_pool_maom: NDArray[np.float32]
    """Organic nitrogen content of the :term:`MAOM` pool [kg N m^-3]."""

    soil_n_pool_ammonium: NDArray[np.float32]
    r"""Soil ammonium (:math:`\ce{NH4+}`) pool [kg N m^-3]."""

    soil_n_pool_nitrate: NDArray[np.float32]
    r"""Soil nitrate (:math:`\ce{NO3-}`) pool [kg N m^-3]."""

    soil_p_pool_dop: NDArray[np.float32]
    """Organic phosphorus content of the low molecular weight carbon pool [kg P m^-3].
    
    This also gets termed the dissolved organic phosphorus (DOP) pool.
    """

    soil_p_pool_particulate: NDArray[np.float32]
    """Organic phosphorus content of the particulate organic matter pool [kg P m^-3]."""

    soil_p_pool_necromass: NDArray[np.float32]
    """Organic phosphorus content of the microbial necromass pool [kg P m^-3]."""

    soil_p_pool_maom: NDArray[np.float32]
    """Organic phosphorus content of the :term:`MAOM` pool [kg P m^-3]."""

    soil_p_pool_primary: NDArray[np.float32]
    """Primary mineral phosphorus pool [kg P m^-3]."""

    soil_p_pool_secondary: NDArray[np.float32]
    """Secondary (inorganic) mineral phosphorus pool [kg P m^-3]."""

    soil_p_pool_labile: NDArray[np.float32]
    """Inorganic labile phosphorus pool [kg P m^-3]."""


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
        pools: dict[str, NDArray[np.float32]],
        constants: SoilConsts,
        functional_groups: dict[str, MicrobialGroupConstants],
        enzyme_classes: dict[str, EnzymeConstants],
        max_depth_of_microbial_activity: float,
    ):
        self.data = data
        """The data object for the Virtual Ecosystem simulation."""

        self.pools = PoolData(**pools)
        """Pools which can change during the soil model update.
        
        These pools need to be added outside the data object otherwise the integrator
        cannot update them and the integration will fail.
        """
        self.constants = constants
        """Set of constants for the soil model."""

        self.functional_groups = functional_groups
        """Set of microbial functional groups used by the soil model."""

        self.enzyme_classes = enzyme_classes
        """Details of the enzyme classes used by the soil model."""

        self.max_depth_of_microbial_activity = max_depth_of_microbial_activity
        """Maximum depth of the soil profile where microbial activity occurs [m]."""

    def calculate_all_pool_updates(
        self,
        delta_pools_ordered: dict[str, NDArray[np.float32]],
        layer_structure: LayerStructure,
        soil_moisture_capacity: float,
        top_soil_layer_thickness: float,
    ) -> NDArray[np.float32]:
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
            soil_moisture_capacity: Soil moisture capacity, i.e. the maximum
                (volumetric) moisture the soil can hold [unitless].
            top_soil_layer_thickness: Thickness of the topsoil layer [mm].

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
        # Calculate the effective saturation of the soil (soil layer thickness needs to
        # be converted from m to mm here to be consistent with soil moisture units)
        # TODO - This needs to be reviewed as part of the soil abiotic links review
        effective_saturation = soil_moisture / (
            soil_moisture_capacity * top_soil_layer_thickness * 1e3
        )

        # Find environmental factors which impact biogeochemical soil processes
        env_factors = calculate_environmental_effect_factors(
            soil_water_potential=soil_water_potential,
            pH=self.data["pH"].to_numpy(),
            clay_fraction=self.data["clay_fraction"].to_numpy(),
            constants=self.constants,
        )
        # find changes related to microbial uptake, growth and decay
        microbial_changes = calculate_microbial_changes(
            pools=self.pools,
            soil_temp=soil_temperature,
            env_factors=env_factors,
            constants=self.constants,
            functional_groups=self.functional_groups,
            enzyme_classes=self.enzyme_classes,
        )
        # find changes driven by the enzyme pools
        enzyme_mediated = calculate_enzyme_mediated_rates(
            pools=self.pools,
            soil_temp=soil_temperature,
            env_factors=env_factors,
            enzyme_classes=self.enzyme_classes,
        )

        # Calculate leaching rates
        nutrient_leaching = calculate_nutrient_leaching(
            soil_c_pool_lmwc=self.pools.soil_c_pool_lmwc,
            soil_n_pool_don=self.pools.soil_n_pool_don,
            soil_p_pool_dop=self.pools.soil_p_pool_dop,
            soil_n_pool_ammonium=self.pools.soil_n_pool_ammonium,
            soil_n_pool_nitrate=self.pools.soil_n_pool_nitrate,
            soil_p_pool_labile=self.pools.soil_p_pool_labile,
            vertical_flow_rate=self.data["vertical_flow"].to_numpy(),
            soil_moisture=soil_moisture,
            constants=self.constants,
        )

        # Calculate transfers between the lmwc, necromass and maom pools
        maom_desorption_to_lmwc = calculate_maom_desorption(
            soil_c_pool_maom=self.pools.soil_c_pool_maom,
            desorption_rate_constant=self.constants.maom_desorption_rate,
        )

        necromass_decay_to_lmwc = calculate_necromass_breakdown(
            soil_c_pool_necromass=self.pools.soil_c_pool_necromass,
            necromass_decay_rate=self.constants.necromass_decay_rate,
        )

        necromass_sorption_to_maom = calculate_sorption_to_maom(
            soil_c_pool=self.pools.soil_c_pool_necromass,
            sorption_rate_constant=self.constants.necromass_sorption_rate,
        )
        lmwc_sorption_to_maom = calculate_sorption_to_maom(
            soil_c_pool=self.pools.soil_c_pool_lmwc,
            sorption_rate_constant=self.constants.lmwc_sorption_rate,
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
            constants=self.constants,
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
            constants=self.constants,
        )
        denitrification_rate = calculate_rate_of_denitrification(
            soil_temp=soil_temperature,
            effective_saturation=effective_saturation,
            soil_n_pool_nitrate=self.pools.soil_n_pool_nitrate,
            constants=self.constants,
        )

        # Calculate rate at which ammonium volatilises as ammonia
        ammonia_volatilisation_rate = np.where(
            self.pools.soil_n_pool_ammonium >= 0.0,
            self.constants.ammonia_volatilisation_rate_constant
            * self.pools.soil_n_pool_ammonium,
            0.0,
        )

        # Calculate rate at which nitrogen is fixed
        symbiotic_nitrogen_fixation = calculate_symbiotic_nitrogen_fixation(
            carbon_supply=self.data["nitrogen_fixation_carbon_supply"].to_numpy(),
            soil_temp=soil_temperature,
            active_depth=self.max_depth_of_microbial_activity,
            constants=self.constants,
        )
        free_living_nitrogen_fixation = calculate_free_living_nitrogen_fixation(
            soil_temp=soil_temperature,
            fixation_at_reference=self.constants.free_living_N_fixation_reference_rate,
            reference_temperature=self.constants.free_living_N_fixation_reference_temp,
            q10_nitrogen_fixation=self.constants.free_living_N_fixation_q10_coefficent,
            active_depth=self.max_depth_of_microbial_activity,
        )

        primary_phosphorus_breakdown = (
            self.constants.primary_phosphorus_breakdown_rate
            * self.pools.soil_p_pool_primary
        )
        net_formation_secondary_P = calculate_net_formation_of_secondary_P(
            soil_p_pool_labile=self.pools.soil_p_pool_labile,
            soil_p_pool_secondary=self.pools.soil_p_pool_secondary,
            secondary_p_breakdown_rate=self.constants.secondary_phosphorus_breakdown_rate,
            labile_p_sorption_rate=self.constants.labile_phosphorus_sorption_rate,
        )

        # Determine net changes to the pools
        delta_pools_ordered["soil_c_pool_lmwc"] = (
            litter_mineralisation_flux.lmwc
            + self.to_per_volume(self.data["root_carbohydrate_exudation"].to_numpy())
            + enzyme_mediated.pom_to_lmwc
            + enzyme_mediated.maom_to_lmwc
            + maom_desorption_to_lmwc
            + necromass_decay_to_lmwc
            - microbial_changes.lmwc_uptake
            - lmwc_sorption_to_maom
            - nutrient_leaching.lmwc
        )

        delta_pools_ordered["soil_c_pool_maom"] = (
            necromass_sorption_to_maom
            + lmwc_sorption_to_maom
            - enzyme_mediated.maom_to_lmwc
            - maom_desorption_to_lmwc
        )
        delta_pools_ordered["soil_c_pool_bacteria"] = microbial_changes.bacteria_change
        delta_pools_ordered["soil_c_pool_fungi"] = microbial_changes.fungi_change
        delta_pools_ordered["soil_c_pool_pom"] = (
            litter_mineralisation_flux.pom - enzyme_mediated.pom_to_lmwc
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
        delta_pools_ordered["soil_n_pool_don"] = (
            litter_mineralisation_flux.don
            + pom_n_mineralisation
            + necromass_outflows["decay_nitrogen"]
            + nutrient_transfers_maom_to_lmwc["nitrogen"]
            - microbial_changes.don_uptake
            - nutrient_leaching.don
        )
        delta_pools_ordered["soil_n_pool_particulate"] = (
            litter_mineralisation_flux.particulate_n - pom_n_mineralisation
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
            self.to_per_volume(self.constants.ammonium_deposition_rate)
            + litter_mineralisation_flux.ammonium
            + symbiotic_nitrogen_fixation
            + free_living_nitrogen_fixation
            - microbial_changes.ammonium_change
            - self.to_per_volume(self.data["plant_ammonium_uptake"].to_numpy())
            - nutrient_leaching.ammonium
            - ammonia_volatilisation_rate
            - nitrification_rate
        )
        delta_pools_ordered["soil_n_pool_nitrate"] = (
            nitrification_rate
            - denitrification_rate
            - microbial_changes.nitrate_change
            - self.to_per_volume(self.data["plant_nitrate_uptake"].to_numpy())
            - nutrient_leaching.nitrate
        )
        delta_pools_ordered["soil_p_pool_dop"] = (
            litter_mineralisation_flux.dop
            + pom_p_mineralisation
            + necromass_outflows["decay_phosphorus"]
            + nutrient_transfers_maom_to_lmwc["phosphorus"]
            - microbial_changes.dop_uptake
            - nutrient_leaching.dop
        )
        delta_pools_ordered["soil_p_pool_particulate"] = (
            litter_mineralisation_flux.particulate_p - pom_p_mineralisation
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
            self.constants.tectonic_uplift_rate_phosphorus
            - primary_phosphorus_breakdown
        )
        delta_pools_ordered["soil_p_pool_secondary"] = net_formation_secondary_P
        delta_pools_ordered["soil_p_pool_labile"] = (
            litter_mineralisation_flux.labile_p
            + self.to_per_volume(self.constants.phosphorus_deposition_rate)
            + primary_phosphorus_breakdown
            - microbial_changes.labile_p_change
            - self.to_per_volume(self.data["plant_phosphorus_uptake"].to_numpy())
            - net_formation_secondary_P
            - nutrient_leaching.labile_P
        )

        # Create output array of pools in desired order
        return np.concatenate(list(delta_pools_ordered.values()))

    def to_per_volume(
        self, input_rate: float | NDArray[np.float32]
    ) -> float | NDArray[np.float32]:
        """Method to convert an external input rate from per area to per volume units.

        Args:
            input_rate: Rate of input to convert [kg m^-2 day^-1].

        Returns:
            Input rate converted to per volume (of the microbial active layer) units [kg
            m^-3 day^-1].
        """

        return input_rate / self.max_depth_of_microbial_activity


def calculate_microbial_changes(
    pools: PoolData,
    soil_temp: NDArray[np.float32],
    env_factors: EnvironmentalEffectFactors,
    constants: SoilConsts,
    functional_groups: dict[str, MicrobialGroupConstants],
    enzyme_classes: dict[str, EnzymeConstants],
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
        functional_groups: Set of microbial functional groups used by the soil model.
        enzyme_classes: Details of the enzyme classes used by the soil model.

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
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        soil_temp=soil_temp,
        constants=constants,
        functional_group=functional_groups["bacteria"],
    )
    bacterial_biomass_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=pools.soil_c_pool_bacteria,
        soil_temp=soil_temp,
        microbial_group=functional_groups["bacteria"],
    )
    fungal_growth, fungal_uptake = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=pools.soil_c_pool_lmwc,
        soil_n_pool_don=pools.soil_n_pool_don,
        soil_n_pool_ammonium=pools.soil_n_pool_ammonium,
        soil_n_pool_nitrate=pools.soil_n_pool_nitrate,
        soil_p_pool_dop=pools.soil_p_pool_dop,
        soil_p_pool_labile=pools.soil_p_pool_labile,
        microbial_pool_size=pools.soil_c_pool_fungi,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        soil_temp=soil_temp,
        constants=constants,
        functional_group=functional_groups["fungi"],
    )
    fungal_biomass_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=pools.soil_c_pool_fungi,
        soil_temp=soil_temp,
        microbial_group=functional_groups["fungi"],
    )

    # Calculate the total production of each enzyme class
    enzyme_production = calculate_enzyme_production(
        microbial_groups=functional_groups,
        growth_rates={"bacteria": bacterial_growth, "fungi": fungal_growth},
    )

    # Find changes in each enzyme pool
    enzyme_changes = calculate_enzyme_changes(
        pools=pools,
        enzyme_production=enzyme_production,
        enzyme_classes=enzyme_classes,
    )

    # Find flow of nitrogen to necromass pool
    necromass_n_flow, necromass_p_flow = calculate_nutrient_flows_to_necromass(
        bacterial_loss=bacterial_biomass_loss,
        fungal_loss=fungal_biomass_loss,
        enzyme_changes=enzyme_changes,
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
    )

    return MicrobialChanges(
        lmwc_uptake=bacterial_uptake.carbon + fungal_uptake.carbon,
        don_uptake=bacterial_uptake.organic_nitrogen + fungal_uptake.organic_nitrogen,
        ammonium_change=bacterial_uptake.ammonium + fungal_uptake.ammonium,
        nitrate_change=bacterial_uptake.nitrate + fungal_uptake.nitrate,
        dop_uptake=(
            bacterial_uptake.organic_phosphorus + fungal_uptake.organic_phosphorus
        ),
        labile_p_change=(
            bacterial_uptake.inorganic_phosphorus + fungal_uptake.inorganic_phosphorus
        ),
        bacteria_change=bacterial_growth - bacterial_biomass_loss,
        fungi_change=fungal_growth - fungal_biomass_loss,
        pom_enzyme_bacteria_change=enzyme_changes.net_change_pom_bacteria,
        maom_enzyme_bacteria_change=enzyme_changes.net_change_maom_bacteria,
        pom_enzyme_fungi_change=enzyme_changes.net_change_pom_fungi,
        maom_enzyme_fungi_change=enzyme_changes.net_change_maom_fungi,
        necromass_generation=(
            enzyme_changes.denaturation_pom_bacteria
            + enzyme_changes.denaturation_maom_bacteria
            + enzyme_changes.denaturation_pom_fungi
            + enzyme_changes.denaturation_maom_fungi
            + bacterial_biomass_loss
            + fungal_biomass_loss
        ),
        necromass_n_flow=necromass_n_flow,
        necromass_p_flow=necromass_p_flow,
    )


def calculate_enzyme_mediated_rates(
    pools: PoolData,
    soil_temp: NDArray[np.float32],
    env_factors: EnvironmentalEffectFactors,
    enzyme_classes: dict[str, EnzymeConstants],
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


def calculate_nutrient_leaching(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_n_pool_don: NDArray[np.float32],
    soil_p_pool_dop: NDArray[np.float32],
    soil_n_pool_ammonium: NDArray[np.float32],
    soil_n_pool_nitrate: NDArray[np.float32],
    soil_p_pool_labile: NDArray[np.float32],
    vertical_flow_rate: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    constants: SoilConsts,
) -> LeachingRates:
    """Calculate the rate a which each soluble nutrient pool is leached.

    Leaching rates are calculated for the low molecular weight carbon pool and the
    inorganic nitrogen and phosphorus pools based on their solubility and the rate at
    which water flows through the soil. The loss of organic nitrogen and phosphorus due
    to leaching is then calculated based on the stoichiometry and leaching rate of the
    LMWC pool.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_n_pool_don: Dissolved organic nitrogen pool [kg N m^-3]
        soil_p_pool_dop: Dissolved organic phosphorus pool [kg P m^-3]
        soil_n_pool_ammonium: Soil ammonium pool [kg N m^-3]
        soil_n_pool_nitrate: Soil nitrate pool [kg N m^-3]
        soil_p_pool_labile: Labile inorganic phosphorus pool [kg P m^-3]
        vertical_flow_rate: Rate of flow downwards through the soil [mm day^-1]
        soil_moisture: Volume of water contained in topsoil layer [mm]
        constants: Set of constants for the soil model.

    Returns:
        A dataclass containing the rate a which each soluble nutrient pool leaches.
    """

    # Find leaching rates
    labile_carbon_leaching = calculate_leaching_rate(
        solute_density=soil_c_pool_lmwc,
        vertical_flow_rate=vertical_flow_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_lmwc,
    )
    ammonium_leaching = calculate_leaching_rate(
        solute_density=soil_n_pool_ammonium,
        vertical_flow_rate=vertical_flow_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_ammonium,
    )
    nitrate_leaching = calculate_leaching_rate(
        solute_density=soil_n_pool_nitrate,
        vertical_flow_rate=vertical_flow_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_nitrate,
    )
    labile_phosphorus_leaching = calculate_leaching_rate(
        solute_density=soil_p_pool_labile,
        vertical_flow_rate=vertical_flow_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=constants.solubility_coefficient_labile_p,
    )

    # Find rate at which don and dop are lost due to lmwc leaching
    c_n_ratio_lmwc = soil_c_pool_lmwc / soil_n_pool_don
    c_p_ratio_lmwc = soil_c_pool_lmwc / soil_p_pool_dop
    don_leaching = labile_carbon_leaching / c_n_ratio_lmwc
    dop_leaching = labile_carbon_leaching / c_p_ratio_lmwc

    return LeachingRates(
        lmwc=labile_carbon_leaching,
        don=don_leaching,
        dop=dop_leaching,
        ammonium=np.where(ammonium_leaching >= 0.0, ammonium_leaching, 0.0),
        nitrate=np.where(nitrate_leaching >= 0.0, nitrate_leaching, 0.0),
        labile_P=np.where(
            labile_phosphorus_leaching >= 0.0, labile_phosphorus_leaching, 0.0
        ),
    )


def calculate_enzyme_changes(
    pools: PoolData,
    enzyme_production: dict[str, NDArray[np.float32]],
    enzyme_classes: dict[str, EnzymeConstants],
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
    enzyme_pool_size: NDArray[np.float32],
    enzyme_production: NDArray[np.float32],
    enzyme_turnover_rate: float,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
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
    growth_rates: dict[str, NDArray[np.float32]],
) -> dict[str, NDArray[np.float32]]:
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

    return {
        f"{group.name}_{substrate}": (
            growth_rates[group.name] * group.enzyme_production[substrate]
        )
        for group in microbial_groups.values()
        for substrate in group.find_enzyme_substrates()
    }


def calculate_maintenance_biomass_synthesis(
    microbe_pool_size: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    microbial_group: MicrobialGroupConstants,
) -> NDArray[np.float32]:
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


def calculate_carbon_use_efficiency(
    soil_temp: NDArray[np.float32],
    reference_cue: float,
    cue_reference_temp: float,
    cue_with_temperature: float,
) -> NDArray[np.float32]:
    """Calculate the (temperature dependant) carbon use efficiency.

    TODO - This should be adapted to use an Arrhenius function at some point.

    Args:
        soil_temp: soil temperature for each soil grid cell [degrees C]
        reference_cue: Carbon use efficiency at reference temp [unitless]
        cue_reference_temp: Reference temperature [degrees C]
        cue_with_temperature: Rate of change in carbon use efficiency with increasing
            temperature [degree C^-1]

    Returns:
        The carbon use efficiency (CUE) of the microbial community
    """

    return reference_cue - cue_with_temperature * (soil_temp - cue_reference_temp)


def calculate_enzyme_turnover(
    enzyme_pool: NDArray[np.float32], turnover_rate: float
) -> NDArray[np.float32]:
    """Calculate the turnover rate of a specific enzyme class.

    Args:
        enzyme_pool: The pool size for the enzyme class in question [kg C m^-3]
        turnover_rate: The rate at which enzymes in the pool turnover [day^-1]

    Returns:
        The rate at which enzymes are lost from the pool [kg C m^-3 day^-1]
    """

    return turnover_rate * enzyme_pool


def calculate_nutrient_uptake_rates(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_n_pool_don: NDArray[np.float32],
    soil_n_pool_ammonium: NDArray[np.float32],
    soil_n_pool_nitrate: NDArray[np.float32],
    soil_p_pool_dop: NDArray[np.float32],
    soil_p_pool_labile: NDArray[np.float32],
    microbial_pool_size: NDArray[np.float32],
    water_factor: NDArray[np.float32],
    pH_factor: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
    functional_group: MicrobialGroupConstants,
) -> tuple[NDArray[np.float32], NetNutrientConsumption]:
    """Calculate the rate at which microbes uptake each nutrient.

    These rates are found based on the assumption that microbial stoichiometry is
    inflexible, i.e. assuming that the rate of uptake of all nutrients (carbon, nitrogen
    and phosphorus) needed for growth will be set by the least available nutrient. The
    carbon case is more complex as carbon gets used both for biomass synthesis and
    respiration. In this case, we calculate the carbon use efficiency and use this to
    find the maximum amount of carbon available for biomass synthesis. Once the most
    limiting nutrient uptake stream is found it is straightforward to find the demand
    for other nutrients. This is because the microbial biomass stoichiometry can only
    remain the same if nutrients are taken up following the same stoichiometry (with an
    adjustment made for carbon use efficiency).

    Biomass synthesis is split between the synthesis of new cellular biomass and the
    production of extracellular enzymes. We assume that extracellular enzymes are always
    produced in fixed proportion to the rate at which new biomass is synthesised. As
    such, we calculate the nutrient costs of synthesising new biomass based on a
    weighted (by relative investment in production) average of the stoichiometry of the
    different enzymes and the microbial group itself.

    The balance of mineralisation and immobilisation rates of inorganic nitrogen and
    phosphorus are also calculated in this function. This is done by calculating the
    difference between the demand for nitrogen and phosphorus and their uptake due to
    organic matter uptake. If more is taken up as a component of organic matter than is
    needed then nutrients are mineralised, i.e. mass is added to the relevant inorganic
    nutrient pool. Conversely, if more is required to meet demand uptake occurs from the
    relevant inorganic nutrient pool (this is termed immobilisation). Two forms
    inorganic nitrogen can be taken up by microbes, ammonium and nitrate. The rate at
    which these are taken up is determined by the ratio of their uptake rates. When
    inorganic nitrogen is mineralised the ratio of ammonium to nitrate mineralised is
    determined by a fixed ratio defined in the model constants.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_n_pool_don: Dissolved organic nitrogen pool [kg N m^-3]
        soil_n_pool_ammonium: Soil ammonium pool [kg N m^-3]
        soil_n_pool_nitrate: Soil nitrate pool [kg N m^-3]
        soil_p_pool_dop: Dissolved organic phosphorus pool [kg P m^-3]
        soil_p_pool_labile: Labile inorganic phosphorus pool [kg P m^-3]
        microbial_pool_size: Amount of biomass for functional of interest [kg C m^-3]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.
        functional_group: A data class containing the parameters defining the microbial
            functional group

    Returns:
        A tuple containing the rate at which microbial (cellular) biomass increases due
        to nutrient uptake, as well as a dataclass containing the rate at which carbon,
        nitrogen and phosphorus get taken up.
    """

    # Calculate highest possible microbial uptake rates for organic matter and inorganic
    # forms of nitrogen and phosphorus
    carbon_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_c_pool_lmwc,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_labile_C,
        half_saturation_constant=functional_group.half_sat_labile_C_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )
    ammonium_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_n_pool_ammonium,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_ammonium,
        half_saturation_constant=functional_group.half_sat_ammonium_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )
    nitrate_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_n_pool_nitrate,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_nitrate,
        half_saturation_constant=functional_group.half_sat_nitrate_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )
    inorganic_phosphorus_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_p_pool_labile,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_labile_p,
        half_saturation_constant=functional_group.half_sat_labile_p_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )

    # Calculate carbon use efficiency and use to determine maximum possible rate of
    # carbon gain
    carbon_use_efficiency = calculate_carbon_use_efficiency(
        soil_temp,
        constants.reference_cue,
        constants.cue_reference_temp,
        constants.cue_with_temperature,
    )
    carbon_gain_max = carbon_uptake_rate_max * carbon_use_efficiency

    # Find stoichiometry of the LMWC pool and use to find maximum possible uptake rates
    # for organic nitrogen and phosphorus
    lmwc_c_n_ratio = soil_c_pool_lmwc / soil_n_pool_don
    lmwc_c_p_ratio = soil_c_pool_lmwc / soil_p_pool_dop
    organic_nitrogen_uptake_rate_max = carbon_uptake_rate_max / lmwc_c_n_ratio
    organic_phosphorus_uptake_rate_max = carbon_uptake_rate_max / lmwc_c_p_ratio

    # Find actual rate of carbon gain based on most limiting uptake rate, then find
    # nutrient gain and total carbon consumption based on this
    actual_carbon_gain = np.minimum.reduce(
        [
            carbon_gain_max,
            functional_group.synthesis_nutrient_ratios["nitrogen"]
            * (
                organic_nitrogen_uptake_rate_max
                + ammonium_uptake_rate_max
                + nitrate_uptake_rate_max
            ),
            functional_group.synthesis_nutrient_ratios["phosphorus"]
            * (
                organic_phosphorus_uptake_rate_max
                + inorganic_phosphorus_uptake_rate_max
            ),
        ]
    )
    actual_carbon_uptake = actual_carbon_gain / carbon_use_efficiency

    # Calculate actual uptake of organic nitrogen and phosphorus based on carbon uptake
    actual_organic_nitrogen_uptake = actual_carbon_uptake / lmwc_c_n_ratio
    actual_organic_phosphorus_uptake = actual_carbon_uptake / lmwc_c_p_ratio

    # Calculate uptake/release of inorganic nitrogen based on difference between
    # stoichiometric demand and organic nitrogen uptake
    nitrogen_demand = (
        actual_carbon_gain / functional_group.synthesis_nutrient_ratios["nitrogen"]
    )
    inorganic_nitrogen_change = nitrogen_demand - actual_organic_nitrogen_uptake

    # For immobilisation of nitrogen, the proportion of ammonium and nitrate taken up
    # follows the proportion of the maximum uptake rates (if either is above zero)
    ammonium_uptake_proportion = np.where(
        (ammonium_uptake_rate_max > 0) | (nitrate_uptake_rate_max > 0),
        ammonium_uptake_rate_max / (ammonium_uptake_rate_max + nitrate_uptake_rate_max),
        0.0,
    )

    # Whether the uptake proportion or the mineralisation proportion is relevant depends
    # whether inorganic nitrogen is being taken up or not
    ammonium_to_nitrate_proportion = np.where(
        inorganic_nitrogen_change > 0,
        ammonium_uptake_proportion,
        constants.ammonium_mineralisation_proportion,
    )
    ammonium_change = inorganic_nitrogen_change * ammonium_to_nitrate_proportion
    nitrate_change = inorganic_nitrogen_change * (1 - ammonium_to_nitrate_proportion)

    # Calculate uptake/release of inorganic phosphorus based on difference between
    # stoichiometric demand and organic phosphorus uptake
    phosphorus_demand = (
        actual_carbon_gain / functional_group.synthesis_nutrient_ratios["phosphorus"]
    )
    inorganic_phosphorus_change = phosphorus_demand - actual_organic_phosphorus_uptake

    consumption_rates = NetNutrientConsumption(
        organic_nitrogen=actual_organic_nitrogen_uptake,
        organic_phosphorus=actual_organic_phosphorus_uptake,
        carbon=actual_carbon_uptake,
        ammonium=ammonium_change,
        nitrate=nitrate_change,
        inorganic_phosphorus=inorganic_phosphorus_change,
    )

    # TODO - the quantities calculated above can be used to calculate the carbon
    # respired instead of being uptaken. This isn't currently of interest, but will be
    # in future

    return actual_carbon_gain / (
        1 + sum(functional_group.enzyme_production.values())
    ), consumption_rates


def calculate_highest_achievable_nutrient_uptake(
    labile_nutrient_pool: NDArray[np.float32],
    microbial_pool_size: NDArray[np.float32],
    water_factor: NDArray[np.float32],
    pH_factor: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    max_uptake_rate: float,
    activation_energy_uptake: float,
    half_saturation_constant: float,
    activation_energy_uptake_saturation: float,
    reference_temperature: float,
) -> NDArray[np.float32]:
    """Calculate highest achievable uptake rate for a specific nutrient.

    This function starts by calculating the impact that environmental factors have on
    the rate and saturation constants for microbial uptake. These constants are then
    used to calculate the maximum possible uptake rate for the specific nutrient and
    microbial group in question.

    Args:
        labile_nutrient_pool: Mass of nutrient that is in a readily uptakeable (labile)
            form [kg nut m^-3]
        microbial_pool_size: Size of microbial biomass (carbon) pool of interest [kg C
            m^-3]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        max_uptake_rate: Maximum possible uptake rate of the nutrient (at reference
            temperature) [day^-1]
        activation_energy_uptake: Activation energy for nutrient uptake for the
            microbial group in question [J K^-1].
        half_saturation_constant: Half saturation constant for nutrient uptake (at
            reference temperature) [kg nut m^-3]
        activation_energy_uptake_saturation: Activation energy for nutrient uptake
            saturation for the microbial group in question [J K^-1].
        reference_temperature: The reference temperature of the Arrhenius equation [C]

    Returns:
        The maximum uptake rate by the soil microbial biomass for the nutrient in
        question.
    """

    # Calculate impact of temperature on the rate and saturation constants
    temp_factor_rate = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=activation_energy_uptake,
        reference_temperature=reference_temperature,
    )
    temp_factor_saturation = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=activation_energy_uptake_saturation,
        reference_temperature=reference_temperature,
    )
    # Rate and saturation constants are then adjusted based on these environmental
    # conditions
    rate_constant = max_uptake_rate * temp_factor_rate * water_factor * pH_factor
    saturation_constant = half_saturation_constant * temp_factor_saturation

    # Calculate both the rate of carbon uptake, and the rate at which this carbon is
    # assimilated into microbial biomass.
    uptake_rate = rate_constant * (
        (labile_nutrient_pool * microbial_pool_size)
        / (labile_nutrient_pool + saturation_constant)
    )

    return np.where(uptake_rate >= 0.0, uptake_rate, 0.0)


def calculate_enzyme_mediated_decomposition(
    soil_c_pool: NDArray[np.float32],
    soil_enzyme: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    env_factors: EnvironmentalEffectFactors,
    enzyme_class: EnzymeConstants,
) -> NDArray[np.float32]:
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
    soil_c_pool_maom: NDArray[np.float32], desorption_rate_constant: float
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
    soil_c_pool: NDArray[np.float32], sorption_rate_constant: float
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
    soil_c_pool_necromass: NDArray[np.float32], necromass_decay_rate: float
) -> NDArray[np.float32]:
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
    litter_C_mineralisation_rate: NDArray[np.float32],
    litter_N_mineralisation_rate: NDArray[np.float32],
    litter_P_mineralisation_rate: NDArray[np.float32],
    constants: SoilConsts,
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
    mineralisation_rate: NDArray[np.float32], litter_leaching_coefficient: float
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
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
    pool_carbon: NDArray[np.float32],
    pool_nutrient: NDArray[np.float32],
    breakdown_rate: NDArray[np.float32],
) -> NDArray[np.float32]:
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
    bacterial_loss: NDArray[np.float32],
    fungal_loss: NDArray[np.float32],
    enzyme_changes: EnzymePoolChanges,
    microbial_groups: dict[str, MicrobialGroupConstants],
    enzyme_classes: dict[str, EnzymeConstants],
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Calculate the rate at which nutrients flow into the necromass pool.

    These flows comprise of the nitrogen and phosphorus content of the dead cells and
    denatured enzymes that flow into the necromass pool.

    Args:
        bacterial_loss: Rate at which bacterial biomass becomes necromass [kg C m^-3
            day^-1]
        fungal_loss: Rate at which fungal biomass becomes necromass [kg C m^-3 day^-1]
        enzyme_changes: Details of the rate change for the soil enzyme pools.
        microbial_groups: Set of microbial functional groups defined in the soil model
        enzyme_classes: Details of the enzyme classes used by the soil model.

    Returns:
        A tuple containing the rates at which nitrogen [kg N m^-3 day^-1] and phosphorus
        [kg P m^-3 day^-1] are added to the soil necromass pool
    """

    # Calculate nutrient flows due to cellular losses
    necromass_n_cellular = (bacterial_loss / microbial_groups["bacteria"].c_n_ratio) + (
        fungal_loss / microbial_groups["fungi"].c_n_ratio
    )
    necromass_p_cellular = (bacterial_loss / microbial_groups["bacteria"].c_p_ratio) + (
        fungal_loss / microbial_groups["fungi"].c_p_ratio
    )

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
    necromass_carbon: NDArray[np.float32],
    necromass_nitrogen: NDArray[np.float32],
    necromass_phosphorus: NDArray[np.float32],
    necromass_decay: NDArray[np.float32],
    necromass_sorption: NDArray[np.float32],
) -> dict[str, NDArray[np.float32]]:
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
    lmwc_carbon: NDArray[np.float32],
    lmwc_nitrogen: NDArray[np.float32],
    lmwc_phosphorus: NDArray[np.float32],
    maom_carbon: NDArray[np.float32],
    maom_nitrogen: NDArray[np.float32],
    maom_phosphorus: NDArray[np.float32],
    maom_breakdown: NDArray[np.float32],
    maom_desorption: NDArray[np.float32],
    lmwc_sorption: NDArray[np.float32],
) -> dict[str, NDArray[np.float32]]:
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
    soil_temp: NDArray[np.float32],
    effective_saturation: NDArray[np.float32],
    soil_n_pool_ammonium: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
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
    soil_temp: NDArray[np.float32],
    effective_saturation: NDArray[np.float32],
    soil_n_pool_nitrate: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
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
    carbon_supply: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    active_depth: float,
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate rate of nitrogen fixation by plant symbionts.

    The nitrogen is considered to be fixed solely in the form of ammonium. This function
    also converts from the per area units the carbon supply (coming from the plant)
    model is defined in, to the per volume units used by the soil model.

    Args:
        carbon_supply: The rate at which carbon is supplied to symbiotic partners by
            plants for the purpose of nitrogen fixation [kg C m^-2 day^-1]
        soil_temp: Temperature of the relevant soil zone [C]
        active_depth: The depth to which the soil is considered to be biologically
            active [m]
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

    carbon_supply_per_volume = carbon_supply / active_depth

    return carbon_supply_per_volume / fixation_carbon_cost


def calculate_free_living_nitrogen_fixation(
    soil_temp: NDArray[np.float32],
    fixation_at_reference: float,
    reference_temperature: float,
    q10_nitrogen_fixation: float,
    active_depth: float,
) -> NDArray[np.float32]:
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
    soil_p_pool_labile: NDArray[np.float32],
    soil_p_pool_secondary: NDArray[np.float32],
    secondary_p_breakdown_rate: float,
    labile_p_sorption_rate: float,
) -> NDArray[np.float32]:
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
