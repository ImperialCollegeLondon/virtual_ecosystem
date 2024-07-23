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


def calculate_lignin_updates(
    lignin_above_structural: NDArray[np.float32],
    lignin_woody: NDArray[np.float32],
    lignin_below_structural: NDArray[np.float32],
    plant_inputs: dict[str, NDArray[np.float32]],
    input_lignin: dict[str, NDArray[np.float32]],
    updated_pools: dict[str, NDArray[np.float32]],
) -> dict[str, NDArray[np.float32]]:
    """Calculate the changes in lignin proportion for the relevant litter pools.

    The relevant pools are the two structural pools, and the dead wood pool. This
    function calculates the total change over the entire time step, so cannot be used in
    an integration process.

    Args:
        lignin_above_structural: Proportion of above ground structural pool which is
            lignin [unitless]
        lignin_woody: Proportion of dead wood pool which is lignin [unitless]
        lignin_below_structural: Proportion of below ground structural pool which is
            lignin [unitless]
        plant_inputs: Dictionary containing the amount of each litter type that is added
            from the plant model in this time step [kg C m^-2]
        input_lignin: Dictionary containing the lignin concentration of the input to
            each of the three lignin containing litter pools [kg lignin kg C^-1]
        updated_pools: Dictionary containing the updated pool densities for all 5 litter
            pools [kg C m^-2]

    Returns:
        Dictionary containing the updated lignin proportions for the 3 relevant litter
        pools (above ground structural, dead wood, and below ground structural) [kg C
        m^-2]
    """

    change_in_lignin_above_structural = calculate_change_in_lignin(
        input_carbon=plant_inputs["above_ground_structural"],
        updated_pool_carbon=updated_pools["above_structural"],
        input_lignin=input_lignin["above_structural"],
        old_pool_lignin=lignin_above_structural,
    )
    change_in_lignin_woody = calculate_change_in_lignin(
        input_carbon=plant_inputs["woody"],
        updated_pool_carbon=updated_pools["woody"],
        input_lignin=input_lignin["woody"],
        old_pool_lignin=lignin_woody,
    )
    change_in_lignin_below_structural = calculate_change_in_lignin(
        input_carbon=plant_inputs["below_ground_structural"],
        updated_pool_carbon=updated_pools["below_structural"],
        input_lignin=input_lignin["below_structural"],
        old_pool_lignin=lignin_below_structural,
    )

    return {
        "above_structural": change_in_lignin_above_structural,
        "woody": change_in_lignin_woody,
        "below_structural": change_in_lignin_below_structural,
    }


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


def calculate_change_in_lignin(
    input_carbon: NDArray[np.float32],
    updated_pool_carbon: NDArray[np.float32],
    input_lignin: NDArray[np.float32],
    old_pool_lignin: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate the change in the lignin concentration of a particular litter pool.

    This change is found by calculating the difference between the previous lignin
    concentration of the pool and the lignin concentration of the inputs. This
    difference is then multiplied by the ratio of the mass of carbon added to pool and
    the final (carbon) mass of the pool.

    Args:
        input_carbon: The total carbon mass of inputs to the litter pool [kg C m^-2]
        updated_pool_carbon: The total carbon mass of the litter pool after inputs and
            decay [kg C m^-2]
        input_lignin: The proportion of the input carbon that is lignin [unitless]
        old_pool_lignin: The proportion of the carbon mass of the original litter pool
            that was lignin [unitless]

    Returns:
        The total change in the lignin concentration of the pool over the full time step
        [unitless]
    """

    return (input_carbon / (updated_pool_carbon)) * (input_lignin - old_pool_lignin)


def calculate_N_mineralisation(
    decay_rates: dict[str, NDArray[np.float32]],
    c_n_ratio_above_metabolic: NDArray[np.float32],
    c_n_ratio_above_structural: NDArray[np.float32],
    c_n_ratio_woody: NDArray[np.float32],
    c_n_ratio_below_metabolic: NDArray[np.float32],
    c_n_ratio_below_structural: NDArray[np.float32],
    active_microbe_depth: float,
) -> dict[str, NDArray[np.float32]]:
    """Function to calculate the amount of nitrogen mineralised by litter decay.

    This function finds the nitrogen mineralisation rate of each litter pool, by
    dividing the rate of decay (in carbon terms) by the carbon:nitrogen stoichiometry of
    each pool. These are then summed to find the total rate of nitrogen mineralisation
    from litter. Finally, this rate is converted from per area units (which the litter
    model works in) to per volume units (which the soil model works in) by dividing the
    rate by the depth of soil considered to be microbially active.

    Args:
        decay_rates: Dictionary containing the rates of decay for all 5 litter pools
            [kg C m^-2 day^-1]
        c_n_ratio_above_metabolic: Carbon nitrogen ratio of above ground metabolic pool
            [unitless]
        c_n_ratio_above_structural: Carbon nitrogen ratio of above ground structural
            pool [unitless]
        c_n_ratio_woody: Carbon nitrogen ratio of woody litter pool [unitless]
        c_n_ratio_below_metabolic: Carbon nitrogen ratio of below ground metabolic pool
            [unitless]
        c_n_ratio_below_structural: Carbon nitrogen ratio of below ground structural
            pool [unitless]
        active_microbe_depth: Maximum depth of microbial activity in the soil layers [m]

    Returns:
        The total rate of nitrogen mineralisation from litter [kg C m^-3 day^-1].
    """

    # Find nitrogen mineralisation rate for each pool
    above_meta_n_mineral = decay_rates["metabolic_above"] / c_n_ratio_above_metabolic
    above_struct_n_mineral = (
        decay_rates["structural_above"] / c_n_ratio_above_structural
    )
    woody_n_mineral = decay_rates["woody"] / c_n_ratio_woody
    below_meta_n_mineral = decay_rates["metabolic_below"] / c_n_ratio_below_metabolic
    below_struct_n_mineral = (
        decay_rates["structural_below"] / c_n_ratio_below_structural
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
