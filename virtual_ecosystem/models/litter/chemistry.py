"""The ``models.litter.chemistry`` module tracks the chemistry of the litter pools. This
involves both the polymer content (i.e. lignin content of the litter), as well as the
litter stoichiometry (i.e. nitrogen and phosphorus content).

The amount of lignin in both the structural pools and the dead wood pool is tracked, but
not for the metabolic pool because by definition it contains no lignin. Nitrogen and
phosphorus content are tracked for every pool.

Nitrogen and phosphorus contents do not have an explicit impact on decay rates, instead
these contents determine how input material is split between pools (see
:mod:`~virtual_ecosystem.models.litter.inputs`), which indirectly captures the
impact of N and P stoichiometry on litter decomposition rates. By contrast, the impact
of lignin on decay rates is directly calculated.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.litter.constants import LitterConsts
from virtual_ecosystem.models.litter.inputs import LitterInputs, average_nutrient_ratios
from virtual_ecosystem.models.litter.losses import LitterLosses


class LitterChemistry:
    """This class handles the chemistry of litter pools.

    This class contains methods to calculate the changes in the litter pool chemistry
    based on the contents of the `data` object, as well as method to calculate total
    mineralisation based on litter pool decay rates.
    """

    def __init__(self, data: Data, constants: LitterConsts):
        self.data = data
        self.structural_to_metabolic_n_ratio = constants.structural_to_metabolic_n_ratio
        self.structural_to_metabolic_p_ratio = constants.structural_to_metabolic_p_ratio

    def calculate_new_pool_chemistries(
        self,
        updated_pools: dict[str, NDArray[np.floating]],
        litter_inputs: LitterInputs,
        litter_losses: LitterLosses,
        original_pools: dict[str, NDArray[np.floating]],
        update_interval: float,
    ) -> dict[str, DataArray]:
        """Method to calculate the updated chemistry of each litter pool.

        All pools contain nitrogen and phosphorus, so this is updated for every pool.
        Only the structural (above and below ground) pools and the woody pools contain
        lignin, so it is only updated for those pools.

        Args:
            updated_pools: Dictionary containing the updated pool densities for all 5
                litter pools [kg C m^-2]
            litter_inputs: An LitterInputs instance containing the total input of each
                plant biomass type, the proportion of the input that goes to the
                relevant metabolic pool for each input type (expect deadwood) and the
                total input into each litter pool.
            litter_losses: An LitterLosses instance containing the total loss of carbon,
                nitrogen and carbon from each litter pool.
            original_pools: The size of each litter pool after animal consumption, but
                before litter inputs and decay [kg C m^-2].
            update_interval: The update interval for the litter model [days]
        """

        # Find lignin and nitrogen contents of the litter input flows
        input_lignin = calculate_litter_input_lignin_concentrations(
            litter_inputs=litter_inputs,
        )
        input_c_n_ratios = calculate_litter_input_nitrogen_ratios(
            litter_inputs=litter_inputs,
            struct_to_meta_nitrogen_ratio=self.structural_to_metabolic_n_ratio,
        )
        input_c_p_ratios = calculate_litter_input_phosphorus_ratios(
            litter_inputs=litter_inputs,
            struct_to_meta_phosphorus_ratio=self.structural_to_metabolic_p_ratio,
        )

        # Then use to find the changes
        change_in_lignin = self.calculate_lignin_updates(
            litter_inputs=litter_inputs,
            input_lignin=input_lignin,
            updated_pools=updated_pools,
        )
        new_c_n_ratios = self.calculate_new_c_n_ratios(
            litter_inputs=litter_inputs,
            input_c_n_ratios=input_c_n_ratios,
            litter_losses=litter_losses,
            original_pools=original_pools,
            update_interval=update_interval,
        )
        new_c_p_ratios = self.calculate_new_c_p_ratios(
            litter_inputs=litter_inputs,
            input_c_p_ratios=input_c_p_ratios,
            litter_losses=litter_losses,
            original_pools=original_pools,
            update_interval=update_interval,
        )

        # List all the variables this function outputs, which are then used to generate
        # the dictionaries to return
        lignin_variable_names = ["above_structural", "woody", "below_structural"]
        nutrient_variable_names = [
            "above_metabolic",
            "above_structural",
            "woody",
            "below_metabolic",
            "below_structural",
        ]

        lignin_changes = {
            f"lignin_{name}": DataArray(
                self.data[f"lignin_{name}"] + change_in_lignin[name], dims="cell_id"
            )
            for name in lignin_variable_names
        }
        nitrogen_new = {
            f"c_n_ratio_{name}": DataArray(new_c_n_ratios[name], dims="cell_id")
            for name in nutrient_variable_names
        }
        phosphorus_new = {
            f"c_p_ratio_{name}": DataArray(new_c_p_ratios[name], dims="cell_id")
            for name in nutrient_variable_names
        }

        return lignin_changes | nitrogen_new | phosphorus_new

    def calculate_lignin_updates(
        self,
        litter_inputs: LitterInputs,
        input_lignin: dict[str, NDArray[np.floating]],
        updated_pools: dict[str, NDArray[np.floating]],
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the changes in lignin proportion for the relevant litter pools.

        The relevant pools are the two structural pools, and the dead wood pool. This
        function calculates the total change over the entire time step, so cannot be
        used in an integration process.

        Args:
            litter_inputs: An LitterInputs instance containing the total input of each
                plant biomass type, the proportion of the input that goes to the
                relevant metabolic pool for each input type (expect deadwood) and the
                total input into each litter pool.
            input_lignin: Dictionary containing the lignin concentration of the input to
                each of the three lignin containing litter pools [kg lignin kg C^-1]
            updated_pools: Dictionary containing the updated pool densities for all 5
                litter pools [kg C m^-2]

        Returns:
            Dictionary containing the updated lignin proportions for the 3 relevant
            litter pools (above ground structural, dead wood, and below ground
            structural) [unitless]
        """

        change_in_lignin_above_structural = calculate_change_in_chemical_concentration(
            input_carbon=litter_inputs.above_structural,
            updated_pool_carbon=updated_pools["above_structural"],
            input_conc=input_lignin["above_structural"],
            old_pool_conc=self.data["lignin_above_structural"].to_numpy(),
        )
        change_in_lignin_woody = calculate_change_in_chemical_concentration(
            input_carbon=litter_inputs.woody,
            updated_pool_carbon=updated_pools["woody"],
            input_conc=input_lignin["woody"],
            old_pool_conc=self.data["lignin_woody"].to_numpy(),
        )
        change_in_lignin_below_structural = calculate_change_in_chemical_concentration(
            input_carbon=litter_inputs.below_structural,
            updated_pool_carbon=updated_pools["below_structural"],
            input_conc=input_lignin["below_structural"],
            old_pool_conc=self.data["lignin_below_structural"].to_numpy(),
        )

        return {
            "above_structural": change_in_lignin_above_structural,
            "woody": change_in_lignin_woody,
            "below_structural": change_in_lignin_below_structural,
        }

    def calculate_new_c_n_ratios(
        self,
        litter_inputs: LitterInputs,
        input_c_n_ratios: dict[str, NDArray[np.floating]],
        litter_losses: LitterLosses,
        original_pools: dict[str, NDArray[np.floating]],
        update_interval: float,
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the new carbon nitrogen ratios for all litter pools.

        This function calculates the total change over the entire time step, so cannot
        be used in an integration process.

        Args:
            litter_inputs: An LitterInputs instance containing the total input of each
                plant biomass type, the proportion of the input that goes to the
                relevant metabolic pool for each input type (expect deadwood) and the
                total input into each litter pool.
            input_c_n_ratios: Dictionary containing the carbon to nitrogen ratios of the
                input to each of the litter pools [unitless]
            litter_losses: An LitterInputs instance containing the total loss of carbon,
                nitrogen and phosphorus from each litter pool.
            original_pools: The size of each litter pool after animal consumption, but
                before litter inputs and decay [kg C m^-2].
            update_interval: The update interval for the litter model [days]

        Returns:
            Dictionary containing the updated carbon nitrogen ratios for all of the
            litter pools [unitless]
        """

        new_c_n_ratio_above_metabolic = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["above_metabolic"],
            input_carbon_rate=litter_inputs.above_metabolic,
            carbon_loss=litter_losses.above_metabolic_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_above_metabolic"].to_numpy(),
            input_c_nut_ratio=input_c_n_ratios["above_metabolic"],
            nutrient_loss=litter_losses.above_metabolic_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_above_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["above_structural"],
            input_carbon_rate=litter_inputs.above_structural,
            carbon_loss=litter_losses.above_structural_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_above_structural"].to_numpy(),
            input_c_nut_ratio=input_c_n_ratios["above_structural"],
            nutrient_loss=litter_losses.above_structural_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_woody = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["woody"],
            input_carbon_rate=litter_inputs.woody,
            carbon_loss=litter_losses.woody_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_woody"].to_numpy(),
            input_c_nut_ratio=input_c_n_ratios["woody"],
            nutrient_loss=litter_losses.woody_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_below_metabolic = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_metabolic"],
            input_carbon_rate=litter_inputs.below_metabolic,
            carbon_loss=litter_losses.below_metabolic_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_below_metabolic"].to_numpy(),
            input_c_nut_ratio=input_c_n_ratios["below_metabolic"],
            nutrient_loss=litter_losses.below_metabolic_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_below_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_structural"],
            input_carbon_rate=litter_inputs.below_structural,
            carbon_loss=litter_losses.below_structural_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_below_structural"].to_numpy(),
            input_c_nut_ratio=input_c_n_ratios["below_structural"],
            nutrient_loss=litter_losses.below_structural_nitrogen,
            update_interval=update_interval,
        )

        return {
            "above_metabolic": new_c_n_ratio_above_metabolic,
            "above_structural": new_c_n_ratio_above_structural,
            "woody": new_c_n_ratio_woody,
            "below_metabolic": new_c_n_ratio_below_metabolic,
            "below_structural": new_c_n_ratio_below_structural,
        }

    def calculate_new_c_p_ratios(
        self,
        litter_inputs: LitterInputs,
        input_c_p_ratios: dict[str, NDArray[np.floating]],
        litter_losses: LitterLosses,
        original_pools: dict[str, NDArray[np.floating]],
        update_interval: float,
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the new carbon phosphorus ratios for all litter pools.

        This function calculates the total change over the entire time step, so cannot
        be used in an integration process.

        Args:
            litter_inputs: An LitterInputs instance containing the total input of each
                plant biomass type, the proportion of the input that goes to the
                relevant metabolic pool for each input type (expect deadwood) and the
                total input into each litter pool.
            input_c_p_ratios: Dictionary containing the carbon to phosphorus ratios of
                the input to each of the litter pools [unitless]
            litter_losses: An LitterInputs instance containing the total loss of carbon,
                nitrogen and phosphorus from each litter pool.
            original_pools: The size of each litter pool after animal consumption, but
                before litter inputs and decay [kg C m^-2].
            update_interval: The update interval for the litter model [days]

        Returns:
            Dictionary containing the updated carbon phosphorus ratios for all of the
            litter pools [unitless]
        """

        new_c_p_ratio_above_metabolic = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["above_metabolic"],
            input_carbon_rate=litter_inputs.above_metabolic,
            carbon_loss=litter_losses.above_metabolic_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_above_metabolic"].to_numpy(),
            input_c_nut_ratio=input_c_p_ratios["above_metabolic"],
            nutrient_loss=litter_losses.above_metabolic_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_above_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["above_structural"],
            input_carbon_rate=litter_inputs.above_structural,
            carbon_loss=litter_losses.above_structural_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_above_structural"].to_numpy(),
            input_c_nut_ratio=input_c_p_ratios["above_structural"],
            nutrient_loss=litter_losses.above_structural_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_woody = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["woody"],
            input_carbon_rate=litter_inputs.woody,
            carbon_loss=litter_losses.woody_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_woody"].to_numpy(),
            input_c_nut_ratio=input_c_p_ratios["woody"],
            nutrient_loss=litter_losses.woody_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_below_metabolic = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_metabolic"],
            input_carbon_rate=litter_inputs.below_metabolic,
            carbon_loss=litter_losses.below_metabolic_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_below_metabolic"].to_numpy(),
            input_c_nut_ratio=input_c_p_ratios["below_metabolic"],
            nutrient_loss=litter_losses.below_metabolic_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_below_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_structural"],
            input_carbon_rate=litter_inputs.below_structural,
            carbon_loss=litter_losses.below_structural_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_below_structural"].to_numpy(),
            input_c_nut_ratio=input_c_p_ratios["below_structural"],
            nutrient_loss=litter_losses.below_structural_phosphorus,
            update_interval=update_interval,
        )

        return {
            "above_metabolic": new_c_p_ratio_above_metabolic,
            "above_structural": new_c_p_ratio_above_structural,
            "woody": new_c_p_ratio_woody,
            "below_metabolic": new_c_p_ratio_below_metabolic,
            "below_structural": new_c_p_ratio_below_structural,
        }


def calculate_litter_input_lignin_concentrations(
    litter_inputs: LitterInputs,
) -> dict[str, NDArray[np.floating]]:
    """Calculate the concentration of lignin for each plant biomass to litter flow.

    By definition the metabolic litter pools do not contain lignin, so all input
    lignin flows to the structural and woody pools. As the input biomass gets split
    between pools, the lignin concentration of the input to the structural pools
    will be higher than it was in the input biomass.

    For the woody litter there's no structural-metabolic split so the lignin
    concentration of the litter input is the same as that of the dead wood
    production. For the below ground structural litter, the total lignin content of
    root input must be found, this is then converted back into a concentration
    relative to the input into the below structural litter pool. For the above
    ground structural litter pool, the same approach is taken with the combined
    total lignin content of the leaf and reproductive matter inputs being found, and
    then converted to a back into a concentration.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.

    Returns:
        Dictionary containing the lignin concentration of the input to each of the
        three lignin containing litter pools (woody, above and below ground
        structural) [kg lignin kg C^-1]
    """

    lignin_proportion_woody = litter_inputs.stem_lignin

    lignin_proportion_below_structural = (
        litter_inputs.root_lignin
        * litter_inputs.root_mass
        / litter_inputs.below_structural
    )

    lignin_proportion_above_structural = (
        (litter_inputs.leaf_lignin * litter_inputs.leaf_mass)
        + (litter_inputs.reprod_lignin * litter_inputs.reprod_mass)
    ) / litter_inputs.above_structural

    return {
        "woody": lignin_proportion_woody,
        "below_structural": lignin_proportion_below_structural,
        "above_structural": lignin_proportion_above_structural,
    }


def calculate_litter_input_nitrogen_ratios(
    litter_inputs: LitterInputs,
    struct_to_meta_nitrogen_ratio: float,
) -> dict[str, NDArray[np.floating]]:
    """Calculate the carbon to nitrogen ratio for each plant biomass to litter flow.

    The ratio for the input to the woody litter pool just matches the ratio of the
    deadwood input. For the below ground pools, the ratios of the flows from root
    turnover into the metabolic and structural pools is calculated. A similar
    approach is taken for the above ground metabolic and structural pools, but here
    a weighted average of the two contributions to each pool (leaf and reproductive
    tissue turnover) must be taken.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.
        struct_to_meta_nitrogen_ratio: Ratio of the carbon to nitrogen ratios of
            structural vs metabolic litter pools [unitless]

    Returns:
        Dictionary containing the carbon to nitrogen ratios of the input to each of
        the pools [unitless]
    """

    # Calculate c_n_ratio split for each (non-wood) input biomass type
    root_c_n_ratio_meta, root_c_n_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=litter_inputs.root_nitrogen,
            metabolic_split=litter_inputs.roots_meta_split,
            struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
        )
    )

    leaf_c_n_ratio_meta, leaf_c_n_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=litter_inputs.leaf_nitrogen,
            metabolic_split=litter_inputs.leaves_meta_split,
            struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
        )
    )

    reprod_c_n_ratio_meta, reprod_c_n_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=litter_inputs.reprod_nitrogen,
            metabolic_split=litter_inputs.reproduct_meta_split,
            struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
        )
    )

    c_n_ratio_below_metabolic = root_c_n_ratio_meta
    c_n_ratio_below_structural = root_c_n_ratio_struct
    c_n_ratio_woody = litter_inputs.deadwood_nitrogen

    # Inputs with multiple sources have to be weighted
    leaf_meta_input = litter_inputs.leaf_mass * litter_inputs.leaves_meta_split
    reprod_meta_input = litter_inputs.reprod_mass * litter_inputs.reproduct_meta_split
    leaf_struct_input = litter_inputs.leaf_mass * (1 - litter_inputs.leaves_meta_split)
    reprod_struct_input = litter_inputs.reprod_mass * (
        1 - litter_inputs.reproduct_meta_split
    )

    c_n_ratio_above_metabolic = average_nutrient_ratios(
        mass_1=leaf_meta_input,
        mass_2=reprod_meta_input,
        nutrient_ratio_1=leaf_c_n_ratio_meta,
        nutrient_ratio_2=reprod_c_n_ratio_meta,
    )
    c_n_ratio_above_structural = average_nutrient_ratios(
        mass_1=leaf_struct_input,
        mass_2=reprod_struct_input,
        nutrient_ratio_1=leaf_c_n_ratio_struct,
        nutrient_ratio_2=reprod_c_n_ratio_struct,
    )

    return {
        "woody": c_n_ratio_woody,
        "below_metabolic": c_n_ratio_below_metabolic,
        "below_structural": c_n_ratio_below_structural,
        "above_metabolic": c_n_ratio_above_metabolic,
        "above_structural": c_n_ratio_above_structural,
    }


def calculate_litter_input_phosphorus_ratios(
    litter_inputs: LitterInputs,
    struct_to_meta_phosphorus_ratio: float,
) -> dict[str, NDArray[np.floating]]:
    """Calculate carbon to phosphorus ratio for each plant biomass to litter flow.

    The ratio for the input to the woody litter pool just matches the ratio of the
    deadwood input. For the below ground pools, the ratios of the flows from root
    turnover into the metabolic and structural pools is calculated. A similar approach
    is taken for the above ground metabolic and structural pools, but here a weighted
    average of the two contributions to each pool (leaf and reproductive tissue
    turnover) must be taken.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.
        struct_to_meta_phosphorus_ratio: Ratio of the carbon to phosphorus ratios of
            structural vs metabolic litter pools [unitless]

    Returns:
        Dictionary containing the carbon to phosphorus ratios of the input to each of
        the pools [unitless]
    """

    # Calculate c_p_ratio split for each (non-wood) input biomass type
    root_c_p_ratio_meta, root_c_p_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=litter_inputs.root_phosphorus,
            metabolic_split=litter_inputs.roots_meta_split,
            struct_to_meta_nutrient_ratio=struct_to_meta_phosphorus_ratio,
        )
    )

    leaf_c_p_ratio_meta, leaf_c_p_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=litter_inputs.leaf_phosphorus,
            metabolic_split=litter_inputs.leaves_meta_split,
            struct_to_meta_nutrient_ratio=struct_to_meta_phosphorus_ratio,
        )
    )

    reprod_c_p_ratio_meta, reprod_c_p_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=litter_inputs.reprod_phosphorus,
            metabolic_split=litter_inputs.reproduct_meta_split,
            struct_to_meta_nutrient_ratio=struct_to_meta_phosphorus_ratio,
        )
    )

    c_p_ratio_below_metabolic = root_c_p_ratio_meta
    c_p_ratio_below_structural = root_c_p_ratio_struct
    c_p_ratio_woody = litter_inputs.deadwood_phosphorus

    # Inputs with multiple sources have to be weighted
    leaf_meta_input = litter_inputs.leaf_mass * litter_inputs.leaves_meta_split
    reprod_meta_input = litter_inputs.reprod_mass * litter_inputs.reproduct_meta_split
    leaf_struct_input = litter_inputs.leaf_mass * (1 - litter_inputs.leaves_meta_split)
    reprod_struct_input = litter_inputs.reprod_mass * (
        1 - litter_inputs.reproduct_meta_split
    )

    c_p_ratio_above_metabolic = average_nutrient_ratios(
        mass_1=leaf_meta_input,
        mass_2=reprod_meta_input,
        nutrient_ratio_1=leaf_c_p_ratio_meta,
        nutrient_ratio_2=reprod_c_p_ratio_meta,
    )
    c_p_ratio_above_structural = average_nutrient_ratios(
        mass_1=leaf_struct_input,
        mass_2=reprod_struct_input,
        nutrient_ratio_1=leaf_c_p_ratio_struct,
        nutrient_ratio_2=reprod_c_p_ratio_struct,
    )

    return {
        "woody": c_p_ratio_woody,
        "below_metabolic": c_p_ratio_below_metabolic,
        "below_structural": c_p_ratio_below_structural,
        "above_metabolic": c_p_ratio_above_metabolic,
        "above_structural": c_p_ratio_above_structural,
    }


def calculate_litter_chemistry_factor(
    lignin_proportion: NDArray[np.floating], lignin_inhibition_factor: float
) -> NDArray[np.floating]:
    """Calculate the effect that litter chemistry has on litter decomposition rates.

    This expression is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        lignin_proportion: The proportion of the polymers in the litter pool that are
            lignin (or similar) [unitless]
        lignin_inhibition_factor: An exponential factor expressing the extent to which
            lignin inhibits the breakdown of litter [unitless]

    Returns:
        A factor that captures the impact of litter chemistry on litter decay rates
    """

    return np.exp(lignin_inhibition_factor * lignin_proportion)


def calculate_updated_pool_nutrient_ratio(
    initial_carbon: NDArray[np.floating],
    input_carbon_rate: NDArray[np.floating],
    carbon_loss: NDArray[np.floating],
    initial_c_nut_ratio: NDArray[np.floating],
    input_c_nut_ratio: NDArray[np.floating],
    nutrient_loss: NDArray[np.floating],
    update_interval: float,
) -> NDArray[np.floating]:
    """Calculate the updated carbon to nutrient ratio for a particular litter pool.

    This function finds the final carbon to nutrient ratio of a litter pool by finding
    the new total amounts of carbon and nutrient in the pool and then taking the ratio.

    Args:
        initial_carbon: The total carbon mass of the litter pool before inputs and decay
            [kg C m^-2]
        input_carbon_rate: The rate of carbon input to the litter pool
            [kg C m^-2 day^-1]
        carbon_loss: Total loss of carbon from the litter pool due to decay [kg C m^-2]
        initial_c_nut_ratio: The carbon to nutrient ratio of the litter pool at the
            start of the update interval [unitless]
        input_c_nut_ratio: The carbon nutrient ratio of the input biomass [unitless]
        nutrient_loss: Total loss of nutrient from the litter pool due to decay
            [kg nutrient m^-2]
        update_interval: The update interval for the litter model [days]

    Returns:
        The new carbon nutrient ratio at the end of the update interval [unitless]
    """

    input_carbon_total = input_carbon_rate * update_interval

    initial_nitrogen = initial_carbon / initial_c_nut_ratio
    input_nitrogen = input_carbon_total / input_c_nut_ratio

    return (initial_carbon + input_carbon_total - carbon_loss) / (
        initial_nitrogen + input_nitrogen - nutrient_loss
    )


def calculate_change_in_chemical_concentration(
    input_carbon: NDArray[np.floating],
    updated_pool_carbon: NDArray[np.floating],
    input_conc: NDArray[np.floating],
    old_pool_conc: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Calculate the change in the chemical concentration of a particular litter pool.

    This change is found by calculating the difference between the previous
    concentration of the pool and the concentration of the inputs. This difference is
    then multiplied by the ratio of the mass of carbon added to pool and the final
    (carbon) mass of the pool. This function can be used for all chemicals of interest,
    i.e. lignin, nitrogen and phosphorus. This function is agnostic to concentration
    type, so either proportions of total carbon or carbon:nutrient ratios can be
    used. However, the concentration type used must be the same for the old pool and the
    litter input.

    Args:
        input_carbon: The total carbon mass of inputs to the litter pool [kg C m^-2]
        updated_pool_carbon: The total carbon mass of the litter pool after inputs and
            decay [kg C m^-2]
        input_conc: The concentration of the chemical of interest in the (carbon) input
            [unitless]
        old_pool_conc: The concentration of the chemical of interest in the original
            litter pool [unitless]

    Returns:
        The total change in the chemical concentration of the pool over the full time
        step [unitless]
    """

    return (input_carbon / updated_pool_carbon) * (input_conc - old_pool_conc)


def calculate_nutrient_split_between_litter_pools(
    input_c_nut_ratio: NDArray[np.floating],
    metabolic_split: NDArray[np.floating],
    struct_to_meta_nutrient_ratio: float,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Function to calculate the split of input nutrients between litter pools.

    Following :cite:t:`kirschbaum_modelling_2002`, we assume that the nutrient content
    of the structural and metabolic litter pools are in a fixed proportion. This ratio
    can vary between nutrients but doesn't vary between above and below ground pools.
    This is a simplifying assumption to allow us to capture the faster turnover of
    nutrients relative to carbon, without having to build (and parametrise) a model
    where every nutrient effects decay rate of every pool.

    Args:
        input_c_nut_ratio: Carbon:nutrient ratio of input organic matter [unitless]
        metabolic_split: Proportion of organic matter input that flows to the metabolic
            litter pool [unitless]
        struct_to_meta_nutrient_ratio: Ratio of the carbon to nutrient ratios of
            structural vs metabolic litter pools [unitless]

    Returns:
        A tuple containing the carbon to nitrogen ratio of the organic matter input to
        the metabolic and structural litter pools, in that order.
    """

    c_nut_ratio_meta_input = input_c_nut_ratio * (
        metabolic_split + (1 - metabolic_split) / struct_to_meta_nutrient_ratio
    )

    c_nut_ratio_struct_input = struct_to_meta_nutrient_ratio * c_nut_ratio_meta_input

    return (c_nut_ratio_meta_input, c_nut_ratio_struct_input)
