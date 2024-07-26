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


class LitterChemistry:
    """This is a class contains the details of the litter pool chemistry."""

    def __init__(self, data: Data):
        self.data = data

    def calculate_new_pool_chemistries(
        self,
        plant_inputs: dict[str, NDArray[np.float32]],
        input_lignin: dict[str, NDArray[np.float32]],
        input_c_n_ratios: dict[str, NDArray[np.float32]],
        updated_pools: dict[str, NDArray[np.float32]],
    ) -> dict[str, DataArray]:
        """Method to calculate the updated chemistry of each litter pool.

        All pools contain nitrogen and phosphorus, so this is updated for every pool.
        Only the structural (above and below ground) pools and the woody pools contain
        lignin, so it is only updated for those pools.

        Args:
            plant_inputs: Dictionary containing the amount of each litter type that is
                added from the plant model in this time step [kg C m^-2]
            input_lignin: Dictionary containing the lignin concentration of the input to
                each of the three lignin containing litter pools [kg lignin kg C^-1]
            input_c_n_ratios: Dictionary containing the carbon nitrogen ratios of the
                input to each of the litter pools [unitless]
            updated_pools: Dictionary containing the updated pool densities for all 5
                litter pools [kg C m^-2]
        """

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

        return {
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
            "c_n_ratio_above_metabolic": DataArray(
                self.data["c_n_ratio_above_metabolic"]
                + change_in_c_n_ratios["above_metabolic"],
                dims="cell_id",
            ),
            "c_n_ratio_above_structural": DataArray(
                self.data["c_n_ratio_above_structural"]
                + change_in_c_n_ratios["above_structural"],
                dims="cell_id",
            ),
            "c_n_ratio_woody": DataArray(
                self.data["c_n_ratio_woody"] + change_in_c_n_ratios["woody"],
                dims="cell_id",
            ),
            "c_n_ratio_below_metabolic": DataArray(
                self.data["c_n_ratio_below_metabolic"]
                + change_in_c_n_ratios["below_metabolic"],
                dims="cell_id",
            ),
            "c_n_ratio_below_structural": DataArray(
                self.data["c_n_ratio_below_structural"]
                + change_in_c_n_ratios["below_structural"],
                dims="cell_id",
            ),
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
            input_c_n_ratios: Dictionary containing the carbon nitrogen ratios of the
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

    def calculate_N_mineralisation(
        self,
        decay_rates: dict[str, NDArray[np.float32]],
        active_microbe_depth: float,
    ) -> dict[str, NDArray[np.float32]]:
        """Method to calculate the amount of nitrogen mineralised by litter decay.

        This function finds the nitrogen mineralisation rate of each litter pool, by
        dividing the rate of decay (in carbon terms) by the carbon:nitrogen
        stoichiometry of each pool. These are then summed to find the total rate of
        nitrogen mineralisation from litter. Finally, this rate is converted from per
        area units (which the litter model works in) to per volume units (which the soil
        model works in) by dividing the rate by the depth of soil considered to be
        microbially active.

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
