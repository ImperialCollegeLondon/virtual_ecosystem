"""The ``models.litter.chemistry`` module tracks the chemistry of the litter pools. This
involves both the polymer content (i.e. lignin content of the litter), as well as the
litter stoichiometry (i.e. nitrogen and phosphorus content).

The amount of lignin in both the structural pools and the dead wood pool is tracked, but
not for the metabolic pool because by definition it contains no lignin. Nitrogen and
phosphorus content are tracked for every pool.

Nitrogen and phosphorus contents do not have an explicit impact on decay rates, instead
these contents determine how input material is split between pools (see
:mod:`~virtual_ecosystem.models.litter.input_partition`), which indirectly captures the
impact of N and P stoichiometry on litter decomposition rates. By contrast, the impact
of lignin on decay rates is directly calculated.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.litter.constants import LitterConsts


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
        plant_inputs: dict[str, NDArray[np.float32]],
        metabolic_splits: dict[str, NDArray[np.float32]],
        updated_pools: dict[str, NDArray[np.float32]],
    ) -> dict[str, DataArray]:
        """Method to calculate the updated chemistry of each litter pool.

        All pools contain nitrogen and phosphorus, so this is updated for every pool.
        Only the structural (above and below ground) pools and the woody pools contain
        lignin, so it is only updated for those pools.

        Args:
            plant_inputs: Dictionary containing the amount of each litter type that is
                added from the plant model in this time step [kg C m^-2]
            metabolic_splits: Dictionary containing the proportion of each input that
                goes to the relevant metabolic pool. This is for three input types:
                leaves, reproductive tissues and roots [unitless]
            updated_pools: Dictionary containing the updated pool densities for all 5
                litter pools [kg C m^-2]
        """

        # Find lignin and nitrogen contents of the litter input flows
        input_lignin = self.calculate_litter_input_lignin_concentrations(
            plant_input_above_struct=plant_inputs["above_ground_structural"],
            plant_input_below_struct=plant_inputs["below_ground_structural"],
        )
        input_c_n_ratios = self.calculate_litter_input_nitrogen_ratios(
            metabolic_splits=metabolic_splits,
            struct_to_meta_nitrogen_ratio=self.structural_to_metabolic_n_ratio,
        )
        input_c_p_ratios = self.calculate_litter_input_phosphorus_ratios(
            metabolic_splits=metabolic_splits,
            struct_to_meta_phosphorus_ratio=self.structural_to_metabolic_p_ratio,
        )

        # Then use to find the changes
        change_in_lignin = self.calculate_lignin_updates(
            plant_inputs=plant_inputs,
            input_lignin=input_lignin,
            updated_pools=updated_pools,
        )
        change_in_c_n_ratios = self.calculate_c_n_ratio_updates(
            plant_inputs=plant_inputs,
            input_c_n_ratios=input_c_n_ratios,
            updated_pools=updated_pools,
        )
        change_in_c_p_ratios = self.calculate_c_p_ratio_updates(
            plant_inputs=plant_inputs,
            input_c_p_ratios=input_c_p_ratios,
            updated_pools=updated_pools,
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
        nitrogen_changes = {
            f"c_n_ratio_{name}": DataArray(
                self.data[f"c_n_ratio_{name}"] + change_in_c_n_ratios[name],
                dims="cell_id",
            )
            for name in nutrient_variable_names
        }
        phosphorus_changes = {
            f"c_p_ratio_{name}": DataArray(
                self.data[f"c_p_ratio_{name}"] + change_in_c_p_ratios[name],
                dims="cell_id",
            )
            for name in nutrient_variable_names
        }

        return lignin_changes | nitrogen_changes | phosphorus_changes

    def calculate_litter_input_lignin_concentrations(
        self,
        plant_input_below_struct: NDArray[np.float32],
        plant_input_above_struct: NDArray[np.float32],
    ) -> dict[str, NDArray[np.float32]]:
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
            plant_input_below_struct: Plant input to below ground structural litter pool
                [kg C m^-2]
            plant_input_above_struct: Plant input to above ground structural litter pool
                [kg C m^-2]

        Returns:
            Dictionary containing the lignin concentration of the input to each of the
            three lignin containing litter pools (woody, above and below ground
            structural) [kg lignin kg C^-1]
        """

        lignin_proportion_woody = self.data["deadwood_lignin"]

        lignin_proportion_below_structural = (
            self.data["root_turnover_lignin"]
            * self.data["root_turnover"]
            / plant_input_below_struct
        )

        lignin_proportion_above_structural = (
            (self.data["leaf_turnover_lignin"] * self.data["leaf_turnover"])
            + (
                self.data["plant_reproductive_tissue_turnover_lignin"]
                * self.data["plant_reproductive_tissue_turnover"]
            )
        ) / plant_input_above_struct

        return {
            "woody": lignin_proportion_woody.to_numpy(),
            "below_structural": lignin_proportion_below_structural.to_numpy(),
            "above_structural": lignin_proportion_above_structural.to_numpy(),
        }

    def calculate_litter_input_nitrogen_ratios(
        self,
        metabolic_splits: dict[str, NDArray[np.float32]],
        struct_to_meta_nitrogen_ratio: float,
    ) -> dict[str, NDArray[np.float32]]:
        """Calculate the carbon to nitrogen ratio for each plant biomass to litter flow.

        The ratio for the input to the woody litter pool just matches the ratio of the
        deadwood input. For the below ground pools, the ratios of the flows from root
        turnover into the metabolic and structural pools is calculated. A similar
        approach is taken for the above ground metabolic and structural pools, but here
        a weighted average of the two contributions to each pool (leaf and reproductive
        tissue turnover) must be taken.

        Args:
            metabolic_splits: Dictionary containing the proportion of each input that
                goes to the relevant metabolic pool. This is for three input types:
                leaves, reproductive tissues and roots [unitless]
            struct_to_meta_nitrogen_ratio: Ratio of the carbon to nitrogen ratios of
                structural vs metabolic litter pools [unitless]

        Returns:
            Dictionary containing the carbon to nitrogen ratios of the input to each of
            the pools [unitless]
        """

        # Calculate c_n_ratio split for each (non-wood) input biomass type
        root_c_n_ratio_meta, root_c_n_ratio_struct = (
            calculate_nutrient_split_between_litter_pools(
                input_c_nut_ratio=self.data["root_turnover_c_n_ratio"].to_numpy(),
                metabolic_split=metabolic_splits["roots"],
                struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
            )
        )

        leaf_c_n_ratio_meta, leaf_c_n_ratio_struct = (
            calculate_nutrient_split_between_litter_pools(
                input_c_nut_ratio=self.data["leaf_turnover_c_n_ratio"].to_numpy(),
                metabolic_split=metabolic_splits["leaves"],
                struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
            )
        )

        reprod_c_n_ratio_meta, reprod_c_n_ratio_struct = (
            calculate_nutrient_split_between_litter_pools(
                input_c_nut_ratio=self.data[
                    "plant_reproductive_tissue_turnover_c_n_ratio"
                ].to_numpy(),
                metabolic_split=metabolic_splits["reproductive"],
                struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
            )
        )

        c_n_ratio_below_metabolic = root_c_n_ratio_meta
        c_n_ratio_below_structural = root_c_n_ratio_struct
        c_n_ratio_woody = self.data["deadwood_c_n_ratio"].to_numpy()
        # Inputs with multiple sources have to be weighted
        c_n_ratio_above_metabolic = np.divide(
            (
                leaf_c_n_ratio_meta
                * self.data["leaf_turnover"]
                * metabolic_splits["leaves"]
            )
            + (
                reprod_c_n_ratio_meta
                * self.data["plant_reproductive_tissue_turnover"]
                * metabolic_splits["reproductive"]
            ),
            (self.data["leaf_turnover"] * metabolic_splits["leaves"])
            + (
                self.data["plant_reproductive_tissue_turnover"]
                * metabolic_splits["reproductive"]
            ),
        )

        c_n_ratio_above_structural = np.divide(
            (
                leaf_c_n_ratio_struct
                * self.data["leaf_turnover"]
                * (1 - metabolic_splits["leaves"])
            )
            + (
                reprod_c_n_ratio_struct
                * self.data["plant_reproductive_tissue_turnover"]
                * (1 - metabolic_splits["reproductive"])
            ),
            (self.data["leaf_turnover"] * (1 - metabolic_splits["leaves"]))
            + (
                self.data["plant_reproductive_tissue_turnover"]
                * (1 - metabolic_splits["reproductive"])
            ),
        )

        return {
            "woody": c_n_ratio_woody,
            "below_metabolic": c_n_ratio_below_metabolic,
            "below_structural": c_n_ratio_below_structural,
            "above_metabolic": c_n_ratio_above_metabolic,
            "above_structural": c_n_ratio_above_structural,
        }

    def calculate_litter_input_phosphorus_ratios(
        self,
        metabolic_splits: dict[str, NDArray[np.float32]],
        struct_to_meta_phosphorus_ratio: float,
    ) -> dict[str, NDArray[np.float32]]:
        """Calculate carbon to phosphorus ratio for each plant biomass to litter flow.

        The ratio for the input to the woody litter pool just matches the ratio of the
        deadwood input. For the below ground pools, the ratios of the flows from root
        turnover into the metabolic and structural pools is calculated. A similar
        approach is taken for the above ground metabolic and structural pools, but here
        a weighted average of the two contributions to each pool (leaf and reproductive
        tissue turnover) must be taken.

        Args:
            metabolic_splits: Dictionary containing the proportion of each input that
                goes to the relevant metabolic pool. This is for three input types:
                leaves, reproductive tissues and roots [unitless]
            struct_to_meta_phosphorus_ratio: Ratio of the carbon to phosphorus ratios of
                structural vs metabolic litter pools [unitless]

        Returns:
            Dictionary containing the carbon to phosphorus ratios of the input to each
            of the pools [unitless]
        """

        # Calculate c_p_ratio split for each (non-wood) input biomass type
        root_c_p_ratio_meta, root_c_p_ratio_struct = (
            calculate_nutrient_split_between_litter_pools(
                input_c_nut_ratio=self.data["root_turnover_c_p_ratio"].to_numpy(),
                metabolic_split=metabolic_splits["roots"],
                struct_to_meta_nutrient_ratio=struct_to_meta_phosphorus_ratio,
            )
        )

        leaf_c_p_ratio_meta, leaf_c_p_ratio_struct = (
            calculate_nutrient_split_between_litter_pools(
                input_c_nut_ratio=self.data["leaf_turnover_c_p_ratio"].to_numpy(),
                metabolic_split=metabolic_splits["leaves"],
                struct_to_meta_nutrient_ratio=struct_to_meta_phosphorus_ratio,
            )
        )

        reprod_c_p_ratio_meta, reprod_c_p_ratio_struct = (
            calculate_nutrient_split_between_litter_pools(
                input_c_nut_ratio=self.data[
                    "plant_reproductive_tissue_turnover_c_p_ratio"
                ].to_numpy(),
                metabolic_split=metabolic_splits["reproductive"],
                struct_to_meta_nutrient_ratio=struct_to_meta_phosphorus_ratio,
            )
        )

        c_p_ratio_below_metabolic = root_c_p_ratio_meta
        c_p_ratio_below_structural = root_c_p_ratio_struct
        c_p_ratio_woody = self.data["deadwood_c_p_ratio"].to_numpy()
        # Inputs with multiple sources have to be weighted
        c_p_ratio_above_metabolic = np.divide(
            (
                leaf_c_p_ratio_meta
                * self.data["leaf_turnover"]
                * metabolic_splits["leaves"]
            )
            + (
                reprod_c_p_ratio_meta
                * self.data["plant_reproductive_tissue_turnover"]
                * metabolic_splits["reproductive"]
            ),
            (self.data["leaf_turnover"] * metabolic_splits["leaves"])
            + (
                self.data["plant_reproductive_tissue_turnover"]
                * metabolic_splits["reproductive"]
            ),
        )

        c_p_ratio_above_structural = np.divide(
            (
                leaf_c_p_ratio_struct
                * self.data["leaf_turnover"]
                * (1 - metabolic_splits["leaves"])
            )
            + (
                reprod_c_p_ratio_struct
                * self.data["plant_reproductive_tissue_turnover"]
                * (1 - metabolic_splits["reproductive"])
            ),
            (self.data["leaf_turnover"] * (1 - metabolic_splits["leaves"]))
            + (
                self.data["plant_reproductive_tissue_turnover"]
                * (1 - metabolic_splits["reproductive"])
            ),
        )

        return {
            "woody": c_p_ratio_woody,
            "below_metabolic": c_p_ratio_below_metabolic,
            "below_structural": c_p_ratio_below_structural,
            "above_metabolic": c_p_ratio_above_metabolic,
            "above_structural": c_p_ratio_above_structural,
        }

    def calculate_lignin_updates(
        self,
        plant_inputs: dict[str, NDArray[np.float32]],
        input_lignin: dict[str, NDArray[np.float32]],
        updated_pools: dict[str, NDArray[np.float32]],
    ) -> dict[str, NDArray[np.float32]]:
        """Calculate the changes in lignin proportion for the relevant litter pools.

        The relevant pools are the two structural pools, and the dead wood pool. This
        function calculates the total change over the entire time step, so cannot be
        used in an integration process.

        Args:
            plant_inputs: Dictionary containing the amount of each litter type that is
                added from the plant model in this time step [kg C m^-2]
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
            input_carbon=plant_inputs["above_ground_structural"],
            updated_pool_carbon=updated_pools["above_structural"],
            input_conc=input_lignin["above_structural"],
            old_pool_conc=self.data["lignin_above_structural"].to_numpy(),
        )
        change_in_lignin_woody = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["woody"],
            updated_pool_carbon=updated_pools["woody"],
            input_conc=input_lignin["woody"],
            old_pool_conc=self.data["lignin_woody"].to_numpy(),
        )
        change_in_lignin_below_structural = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["below_ground_structural"],
            updated_pool_carbon=updated_pools["below_structural"],
            input_conc=input_lignin["below_structural"],
            old_pool_conc=self.data["lignin_below_structural"].to_numpy(),
        )

        return {
            "above_structural": change_in_lignin_above_structural,
            "woody": change_in_lignin_woody,
            "below_structural": change_in_lignin_below_structural,
        }

    def calculate_c_n_ratio_updates(
        self,
        plant_inputs: dict[str, NDArray[np.float32]],
        input_c_n_ratios: dict[str, NDArray[np.float32]],
        updated_pools: dict[str, NDArray[np.float32]],
    ) -> dict[str, NDArray[np.float32]]:
        """Calculate the changes in carbon nitrogen ratios for all litter pools.

        This function calculates the total change over the entire time step, so cannot
        be used in an integration process.

        Args:
            plant_inputs: Dictionary containing the amount of each litter type that is
                added from the plant model in this time step [kg C m^-2]
            input_c_n_ratios: Dictionary containing the carbon to nitrogen ratios of the
                input to each of the litter pools [unitless]
            updated_pools: Dictionary containing the updated pool densities for all 5
                litter pools [kg C m^-2]

        Returns:
            Dictionary containing the updated carbon nitrogen ratios for all of the
            litter pools [unitless]
        """

        change_in_n_above_metabolic = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["above_ground_metabolic"],
            updated_pool_carbon=updated_pools["above_metabolic"],
            input_conc=input_c_n_ratios["above_metabolic"],
            old_pool_conc=self.data["c_n_ratio_above_metabolic"].to_numpy(),
        )
        change_in_n_above_structural = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["above_ground_structural"],
            updated_pool_carbon=updated_pools["above_structural"],
            input_conc=input_c_n_ratios["above_structural"],
            old_pool_conc=self.data["c_n_ratio_above_structural"].to_numpy(),
        )
        change_in_n_woody = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["woody"],
            updated_pool_carbon=updated_pools["woody"],
            input_conc=input_c_n_ratios["woody"],
            old_pool_conc=self.data["c_n_ratio_woody"].to_numpy(),
        )
        change_in_n_below_metabolic = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["below_ground_metabolic"],
            updated_pool_carbon=updated_pools["below_metabolic"],
            input_conc=input_c_n_ratios["below_metabolic"],
            old_pool_conc=self.data["c_n_ratio_below_metabolic"].to_numpy(),
        )
        change_in_n_below_structural = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["below_ground_structural"],
            updated_pool_carbon=updated_pools["below_structural"],
            input_conc=input_c_n_ratios["below_structural"],
            old_pool_conc=self.data["c_n_ratio_below_structural"].to_numpy(),
        )

        return {
            "above_metabolic": change_in_n_above_metabolic,
            "above_structural": change_in_n_above_structural,
            "woody": change_in_n_woody,
            "below_metabolic": change_in_n_below_metabolic,
            "below_structural": change_in_n_below_structural,
        }

    def calculate_c_p_ratio_updates(
        self,
        plant_inputs: dict[str, NDArray[np.float32]],
        input_c_p_ratios: dict[str, NDArray[np.float32]],
        updated_pools: dict[str, NDArray[np.float32]],
    ) -> dict[str, NDArray[np.float32]]:
        """Calculate the changes in carbon phosphorus ratios for all litter pools.

        This function calculates the total change over the entire time step, so cannot
        be used in an integration process.

        Args:
            plant_inputs: Dictionary containing the amount of each litter type that is
                added from the plant model in this time step [kg C m^-2]
            input_c_p_ratios: Dictionary containing the carbon to phosphorus ratios of
                the input to each of the litter pools [unitless]
            updated_pools: Dictionary containing the updated pool densities for all 5
                litter pools [kg C m^-2]

        Returns:
            Dictionary containing the updated carbon phosphorus ratios for all of the
            litter pools [unitless]
        """

        change_in_p_above_metabolic = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["above_ground_metabolic"],
            updated_pool_carbon=updated_pools["above_metabolic"],
            input_conc=input_c_p_ratios["above_metabolic"],
            old_pool_conc=self.data["c_p_ratio_above_metabolic"].to_numpy(),
        )
        change_in_p_above_structural = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["above_ground_structural"],
            updated_pool_carbon=updated_pools["above_structural"],
            input_conc=input_c_p_ratios["above_structural"],
            old_pool_conc=self.data["c_p_ratio_above_structural"].to_numpy(),
        )
        change_in_p_woody = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["woody"],
            updated_pool_carbon=updated_pools["woody"],
            input_conc=input_c_p_ratios["woody"],
            old_pool_conc=self.data["c_p_ratio_woody"].to_numpy(),
        )
        change_in_p_below_metabolic = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["below_ground_metabolic"],
            updated_pool_carbon=updated_pools["below_metabolic"],
            input_conc=input_c_p_ratios["below_metabolic"],
            old_pool_conc=self.data["c_p_ratio_below_metabolic"].to_numpy(),
        )
        change_in_p_below_structural = calculate_change_in_chemical_concentration(
            input_carbon=plant_inputs["below_ground_structural"],
            updated_pool_carbon=updated_pools["below_structural"],
            input_conc=input_c_p_ratios["below_structural"],
            old_pool_conc=self.data["c_p_ratio_below_structural"].to_numpy(),
        )

        return {
            "above_metabolic": change_in_p_above_metabolic,
            "above_structural": change_in_p_above_structural,
            "woody": change_in_p_woody,
            "below_metabolic": change_in_p_below_metabolic,
            "below_structural": change_in_p_below_structural,
        }

    def calculate_N_mineralisation(
        self,
        decay_rates: dict[str, NDArray[np.float32]],
        active_microbe_depth: float,
    ) -> dict[str, NDArray[np.float32]]:
        """Method to calculate the amount of nitrogen mineralised by litter decay.

        This function finds the nitrogen mineralisation rate of each litter pool, by
        dividing the rate of decay (in carbon terms) by the carbon to nitrogen ratio of
        each pool. These are then summed to find the total rate of nitrogen
        mineralisation from litter. Finally, this rate is converted from per area units
        (which the litter model works in) to per volume units (which the soil model
        works in) by dividing the rate by the depth of soil considered to be microbially
        active.

        Args:
            decay_rates: Dictionary containing the rates of decay for all 5 litter pools
                [kg C m^-2 day^-1]
            active_microbe_depth: Maximum depth of microbial activity in the soil layers
                [m]

        Returns:
            The total rate of nitrogen mineralisation from litter [kg C m^-3 day^-1].
        """

        # Find nitrogen mineralisation rate for each pool
        above_meta_n_mineral = (
            decay_rates["metabolic_above"] / self.data["c_n_ratio_above_metabolic"]
        )
        above_struct_n_mineral = (
            decay_rates["structural_above"] / self.data["c_n_ratio_above_structural"]
        )
        woody_n_mineral = decay_rates["woody"] / self.data["c_n_ratio_woody"]
        below_meta_n_mineral = (
            decay_rates["metabolic_below"] / self.data["c_n_ratio_below_metabolic"]
        )
        below_struct_n_mineral = (
            decay_rates["structural_below"] / self.data["c_n_ratio_below_structural"]
        )

        # Sum them to find total rate of nitrogen mineralisation
        total_N_mineralisation_rate = (
            above_meta_n_mineral
            + above_struct_n_mineral
            + woody_n_mineral
            + below_meta_n_mineral
            + below_struct_n_mineral
        )

        # Convert from per area to per volume units
        return total_N_mineralisation_rate / active_microbe_depth


def calculate_litter_chemistry_factor(
    lignin_proportion: NDArray[np.float32], lignin_inhibition_factor: float
) -> NDArray[np.float32]:
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


def calculate_change_in_chemical_concentration(
    input_carbon: NDArray[np.float32],
    updated_pool_carbon: NDArray[np.float32],
    input_conc: NDArray[np.float32],
    old_pool_conc: NDArray[np.float32],
) -> NDArray[np.float32]:
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
    input_c_nut_ratio: NDArray[np.float32],
    metabolic_split: NDArray[np.float32],
    struct_to_meta_nutrient_ratio: float,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
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

    c_n_ratio_meta_input = np.divide(
        input_c_nut_ratio,
        metabolic_split + struct_to_meta_nutrient_ratio * (1 - metabolic_split),
    )

    c_n_ratio_struct_input = struct_to_meta_nutrient_ratio * c_n_ratio_meta_input

    return (c_n_ratio_meta_input, c_n_ratio_struct_input)
