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
from virtual_ecosystem.models.litter.inputs import InputChemistries, LitterInputs
from virtual_ecosystem.models.litter.losses import LitterLosses


class LitterChemistry:
    """This class handles the chemistry of litter pools.

    This class contains methods to calculate the changes in the litter pool chemistry
    based on the contents of the `data` object, as well as method to calculate total
    mineralisation based on litter pool decay rates.
    """

    def __init__(self, data: Data):
        self.data = data

    def calculate_new_pool_chemistries(
        self,
        litter_inputs: LitterInputs,
        litter_losses: LitterLosses,
        input_chemistries: InputChemistries,
        original_pools: dict[str, NDArray[np.floating]],
        update_interval: float,
    ) -> dict[str, DataArray]:
        """Method to calculate the updated chemistry of each litter pool.

        All pools contain nitrogen and phosphorus, so this is updated for every pool.
        Only the structural (above and below ground) pools and the woody pools contain
        lignin, so it is only updated for those pools.

        Args:
            litter_inputs: An LitterInputs instance containing the total input of each
                plant biomass type, the proportion of the input that goes to the
                relevant metabolic pool for each input type (expect deadwood) and the
                total input into each litter pool.
            litter_losses: An LitterLosses instance containing the total loss of carbon,
                nitrogen and carbon from each litter pool.
            input_chemistries: An InputChemistries instance containing the chemical
                compositions of the input to each litter pool
            original_pools: The size of each litter pool after animal consumption, but
                before litter inputs and decay [kg C m^-2].
            update_interval: The update interval for the litter model [days]
        """

        # Then use to find the changes
        new_lignin_proportions = self.calculate_new_lignin_proportions(
            litter_inputs=litter_inputs,
            input_chemistries=input_chemistries,
            litter_losses=litter_losses,
            original_pools=original_pools,
            update_interval=update_interval,
        )
        new_c_n_ratios = self.calculate_new_c_n_ratios(
            litter_inputs=litter_inputs,
            input_chemistries=input_chemistries,
            litter_losses=litter_losses,
            original_pools=original_pools,
            update_interval=update_interval,
        )
        new_c_p_ratios = self.calculate_new_c_p_ratios(
            litter_inputs=litter_inputs,
            input_chemistries=input_chemistries,
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

        lignin_new = {
            f"lignin_{name}": DataArray(new_lignin_proportions[name], dims="cell_id")
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

        return lignin_new | nitrogen_new | phosphorus_new

    def calculate_new_lignin_proportions(
        self,
        litter_inputs: LitterInputs,
        input_chemistries: InputChemistries,
        litter_losses: LitterLosses,
        original_pools: dict[str, NDArray[np.floating]],
        update_interval: float,
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the new lignin proportions for the relevant litter pools.

        The relevant pools are the two structural pools, and the dead wood pool. This
        function calculates the total change over the entire time step, so cannot be
        used in an integration process.

        Args:
            litter_inputs: An LitterInputs instance containing the total input of each
                plant biomass type, the proportion of the input that goes to the
                relevant metabolic pool for each input type (expect deadwood) and the
                total input into each litter pool.
            input_chemistries: The chemical compositions of the input to each litter
                pool
            litter_losses: An LitterInputs instance containing the total loss of carbon,
                nitrogen, phosphorus and lignin from each litter pool.
            original_pools: The size of each litter pool after animal consumption, but
                before litter inputs and decay [kg C m^-2].
            update_interval: The update interval for the litter model [days]

        Returns:
            Dictionary containing the updated lignin proportions for the 3 relevant
            litter pools (above ground structural, dead wood, and below ground
            structural) [kg lignin C (kg C)^-1]
        """

        new_lignin_proportion_above_struct = calculate_updated_pool_lignin_proportion(
            initial_carbon=original_pools["above_structural"],
            input_carbon_rate=litter_inputs.above_structural,
            carbon_loss=litter_losses.above_structural_carbon,
            initial_lignin_proportion=self.data["lignin_above_structural"].to_numpy(),
            input_lignin_proportion=input_chemistries.above_structural_lignin,
            lignin_loss=litter_losses.above_structural_lignin,
            update_interval=update_interval,
        )
        new_lignin_proportion_woody = calculate_updated_pool_lignin_proportion(
            initial_carbon=original_pools["woody"],
            input_carbon_rate=litter_inputs.woody,
            carbon_loss=litter_losses.woody_carbon,
            initial_lignin_proportion=self.data["lignin_woody"].to_numpy(),
            input_lignin_proportion=input_chemistries.woody_lignin,
            lignin_loss=litter_losses.woody_lignin,
            update_interval=update_interval,
        )
        new_lignin_proportion_below_struct = calculate_updated_pool_lignin_proportion(
            initial_carbon=original_pools["below_structural"],
            input_carbon_rate=litter_inputs.below_structural,
            carbon_loss=litter_losses.below_structural_carbon,
            initial_lignin_proportion=self.data["lignin_below_structural"].to_numpy(),
            input_lignin_proportion=input_chemistries.below_structural_lignin,
            lignin_loss=litter_losses.below_structural_lignin,
            update_interval=update_interval,
        )

        return {
            "above_structural": new_lignin_proportion_above_struct,
            "woody": new_lignin_proportion_woody,
            "below_structural": new_lignin_proportion_below_struct,
        }

    def calculate_new_c_n_ratios(
        self,
        litter_inputs: LitterInputs,
        input_chemistries: InputChemistries,
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
            input_chemistries: The chemical compositions of the input to each litter
                pool
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
            input_c_nut_ratio=input_chemistries.above_metabolic_nitrogen,
            nutrient_loss=litter_losses.above_metabolic_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_above_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["above_structural"],
            input_carbon_rate=litter_inputs.above_structural,
            carbon_loss=litter_losses.above_structural_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_above_structural"].to_numpy(),
            input_c_nut_ratio=input_chemistries.above_structural_nitrogen,
            nutrient_loss=litter_losses.above_structural_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_woody = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["woody"],
            input_carbon_rate=litter_inputs.woody,
            carbon_loss=litter_losses.woody_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_woody"].to_numpy(),
            input_c_nut_ratio=input_chemistries.woody_nitrogen,
            nutrient_loss=litter_losses.woody_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_below_metabolic = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_metabolic"],
            input_carbon_rate=litter_inputs.below_metabolic,
            carbon_loss=litter_losses.below_metabolic_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_below_metabolic"].to_numpy(),
            input_c_nut_ratio=input_chemistries.below_metabolic_nitrogen,
            nutrient_loss=litter_losses.below_metabolic_nitrogen,
            update_interval=update_interval,
        )
        new_c_n_ratio_below_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_structural"],
            input_carbon_rate=litter_inputs.below_structural,
            carbon_loss=litter_losses.below_structural_carbon,
            initial_c_nut_ratio=self.data["c_n_ratio_below_structural"].to_numpy(),
            input_c_nut_ratio=input_chemistries.below_structural_nitrogen,
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
        input_chemistries: InputChemistries,
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
            input_chemistries: The chemical compositions of the input to each litter
                pool
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
            input_c_nut_ratio=input_chemistries.above_metabolic_phosphorus,
            nutrient_loss=litter_losses.above_metabolic_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_above_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["above_structural"],
            input_carbon_rate=litter_inputs.above_structural,
            carbon_loss=litter_losses.above_structural_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_above_structural"].to_numpy(),
            input_c_nut_ratio=input_chemistries.above_structural_phosphorus,
            nutrient_loss=litter_losses.above_structural_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_woody = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["woody"],
            input_carbon_rate=litter_inputs.woody,
            carbon_loss=litter_losses.woody_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_woody"].to_numpy(),
            input_c_nut_ratio=input_chemistries.woody_phosphorus,
            nutrient_loss=litter_losses.woody_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_below_metabolic = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_metabolic"],
            input_carbon_rate=litter_inputs.below_metabolic,
            carbon_loss=litter_losses.below_metabolic_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_below_metabolic"].to_numpy(),
            input_c_nut_ratio=input_chemistries.below_metabolic_phosphorus,
            nutrient_loss=litter_losses.below_metabolic_phosphorus,
            update_interval=update_interval,
        )
        new_c_p_ratio_below_structural = calculate_updated_pool_nutrient_ratio(
            initial_carbon=original_pools["below_structural"],
            input_carbon_rate=litter_inputs.below_structural,
            carbon_loss=litter_losses.below_structural_carbon,
            initial_c_nut_ratio=self.data["c_p_ratio_below_structural"].to_numpy(),
            input_c_nut_ratio=input_chemistries.below_structural_phosphorus,
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


def calculate_litter_chemistry_factor(
    lignin_proportion: NDArray[np.floating], lignin_inhibition_factor: float
) -> NDArray[np.floating]:
    """Calculate the effect that litter chemistry has on litter decomposition rates.

    This expression is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        lignin_proportion: The proportion of litter pool carbon that is held in the form
            of lignin (or similar polymers) [kg lignin C (kg C)^-1]
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

    initial_nutrient = initial_carbon / initial_c_nut_ratio
    input_nutrient = input_carbon_total / input_c_nut_ratio

    return (initial_carbon + input_carbon_total - carbon_loss) / (
        initial_nutrient + input_nutrient - nutrient_loss
    )


def calculate_updated_pool_lignin_proportion(
    initial_carbon: NDArray[np.floating],
    input_carbon_rate: NDArray[np.floating],
    carbon_loss: NDArray[np.floating],
    initial_lignin_proportion: NDArray[np.floating],
    input_lignin_proportion: NDArray[np.floating],
    lignin_loss: NDArray[np.floating],
    update_interval: float,
) -> NDArray[np.floating]:
    """Calculate the change in the lignin proportion of a particular litter pool.

    The lignin proportion of the pool after the update is found by calculating the total
    amounts of carbon (in any form) and lignin carbon, and then dividing to find the
    proportion.

    Args:
        initial_carbon: The total carbon mass of the litter pool before inputs and decay
            [kg C m^-2]
        input_carbon_rate: The rate of carbon input to the litter pool
            [kg C m^-2 day^-1]
        carbon_loss: Total loss of carbon from the litter pool due to decay [kg C m^-2]
        initial_lignin_proportion: The lignin proportion of the litter pool at the
            start of the update interval [kg lignin C (kg C)^-1]
        input_lignin_proportion: The lignin proportion of the input biomass
            [kg lignin C (kg C)^-1]
        lignin_loss: Total loss of lignin from the litter pool due to decay
            [kg lignin C m^-2]
        update_interval: The update interval for the litter model [days]

    Returns:
        The new lignin proportion at the end of the update interval
        [kg lignin C (kg C)^-1]
    """

    input_carbon_total = input_carbon_rate * update_interval

    initial_lignin = initial_carbon * initial_lignin_proportion
    input_lignin = input_carbon_total * input_lignin_proportion

    return (initial_lignin + input_lignin - lignin_loss) / (
        initial_carbon + input_carbon_total - carbon_loss
    )
