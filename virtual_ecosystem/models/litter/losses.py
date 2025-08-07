"""The ``models.litter.losses`` module handles the calculation of the total loss of each
nutrient (carbon, nitrogen and phosphorus) from each litter pool, as well as the total
mineralisation rate to soil of each nutrient.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.models.litter.inputs import LitterInputs


@dataclass(frozen=True)
class LitterLosses:
    """The full set losses for the litter pools."""

    above_metabolic_carbon: NDArray[np.floating]
    """Carbon loss rate from the aboveground metabolic pool [kg C m^-2 day^-1]"""
    above_structural_carbon: NDArray[np.floating]
    """Carbon loss rate from the aboveground structural pool [kg C m^-2 day^-1]"""
    woody_carbon: NDArray[np.floating]
    """Carbon loss rate from the woody pool [kg C m^-2 day^-1]"""
    below_metabolic_carbon: NDArray[np.floating]
    """Carbon loss rate from the belowground metabolic pool [kg C m^-2 day^-1]"""
    below_structural_carbon: NDArray[np.floating]
    """Carbon loss rate from the belowground structural pool [kg C m^-2 day^-1]"""


def calculate_litter_losses(
    original_pools: dict[str, NDArray[np.floating]],
    final_pools: dict[str, NDArray[np.floating]],
    litter_inputs: LitterInputs,
    update_interval: float,
) -> LitterLosses:
    """Calculate the loss of carbon, nitrogen and phosphorus from each litter pool.

    Args:
        original_pools: Pool sizes before any litter input and decay [kg C m^-2].
        final_pools: Pool sizes after litter input and decay [kg C m^-2].
        litter_inputs: The inputs to each litter pool [kg C m^-2 day^-1].
        update_interval: The time period over which the litter pools are updated [days].

    Returns:
        A dataclass containing the total losses of each nutrient from each litter pool,
        as well as the total mineralisation rates to the soil for each nutrient.
    """

    return LitterLosses(
        above_metabolic_carbon=calculate_carbon_pool_loss(
            old_pool_size=original_pools["above_metabolic"],
            final_pool_size=final_pools["above_metabolic"],
            input_rate=litter_inputs.above_metabolic,
            update_interval=update_interval,
        ),
        above_structural_carbon=calculate_carbon_pool_loss(
            old_pool_size=original_pools["above_structural"],
            final_pool_size=final_pools["above_structural"],
            input_rate=litter_inputs.above_structural,
            update_interval=update_interval,
        ),
        woody_carbon=calculate_carbon_pool_loss(
            old_pool_size=original_pools["woody"],
            final_pool_size=final_pools["woody"],
            input_rate=litter_inputs.woody,
            update_interval=update_interval,
        ),
        below_metabolic_carbon=calculate_carbon_pool_loss(
            old_pool_size=original_pools["below_metabolic"],
            final_pool_size=final_pools["below_metabolic"],
            input_rate=litter_inputs.below_metabolic,
            update_interval=update_interval,
        ),
        below_structural_carbon=calculate_carbon_pool_loss(
            old_pool_size=original_pools["below_structural"],
            final_pool_size=final_pools["below_structural"],
            input_rate=litter_inputs.below_structural,
            update_interval=update_interval,
        ),
    )


def calculate_carbon_pool_loss(
    old_pool_size: NDArray[np.floating],
    final_pool_size: NDArray[np.floating],
    input_rate: NDArray[np.floating],
    update_interval: float,
) -> NDArray[np.floating]:
    """Calculate the total loss of carbon from a specific litter pool.

    New carbon is added over the update interval so this has to be accounted for in the
    calculation of the loss.

    Args:
        old_pool_size: The size of the litter pool before the update [kg C m^-2].
        final_pool_size: The size of the litter pool after the update [kg C m^-2].
        input_rate: The rate of carbon input to the litter pool [kg C m^-2 day^-1].
        update_interval: The time period over which the litter pools are updated [days].
    """

    return old_pool_size + (input_rate * update_interval) - final_pool_size
