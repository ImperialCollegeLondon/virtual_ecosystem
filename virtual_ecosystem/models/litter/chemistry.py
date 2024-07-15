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
    input_carbon: float | NDArray[np.float32],
    updated_pool_carbon: NDArray[np.float32],
    input_lignin: float | NDArray[np.float32],
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
