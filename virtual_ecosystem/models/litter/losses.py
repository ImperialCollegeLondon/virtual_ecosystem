"""The ``models.litter.losses`` module handles the calculation of the total loss of each
nutrient (carbon, nitrogen and phosphorus) from each litter pool, as well as the total
mineralisation rate to soil of each nutrient.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.litter.inputs import LitterInputs


@dataclass(frozen=True)
class LitterLosses:
    """The full set losses for the litter pools, as well as the mineralisation rates."""

    above_metabolic_carbon: NDArray[np.floating]
    """Carbon loss rate from the aboveground metabolic pool [kg C m^-2]"""
    above_structural_carbon: NDArray[np.floating]
    """Carbon loss rate from the aboveground structural pool [kg C m^-2]"""
    woody_carbon: NDArray[np.floating]
    """Carbon loss rate from the woody pool [kg C m^-2]"""
    below_metabolic_carbon: NDArray[np.floating]
    """Carbon loss rate from the belowground metabolic pool [kg C m^-2]"""
    below_structural_carbon: NDArray[np.floating]
    """Carbon loss rate from the belowground structural pool [kg C m^-2]"""

    above_metabolic_nitrogen: NDArray[np.floating]
    """Nitrogen loss rate from the aboveground metabolic pool [kg N m^-2]"""
    above_structural_nitrogen: NDArray[np.floating]
    """Nitrogen loss rate from the aboveground structural pool [kg N m^-2]"""
    woody_nitrogen: NDArray[np.floating]
    """Nitrogen loss rate from the woody pool [kg N m^-2]"""
    below_metabolic_nitrogen: NDArray[np.floating]
    """Nitrogen loss rate from the belowground metabolic pool [kg N m^-2]"""
    below_structural_nitrogen: NDArray[np.floating]
    """Nitrogen loss rate from the belowground structural pool [kg N m^-2]"""

    above_metabolic_phosphorus: NDArray[np.floating]
    """Phosphorus loss rate from the aboveground metabolic pool [kg P m^-2]"""
    above_structural_phosphorus: NDArray[np.floating]
    """Phosphorus loss rate from the aboveground structural pool [kg P m^-2]"""
    woody_phosphorus: NDArray[np.floating]
    """Phosphorus loss rate from the woody pool [kg P m^-2]"""
    below_metabolic_phosphorus: NDArray[np.floating]
    """Phosphorus loss rate from the belowground metabolic pool [kg P m^-2]"""
    below_structural_phosphorus: NDArray[np.floating]
    """Phosphorus loss rate from the belowground structural pool [kg P m^-2]"""

    above_structural_lignin: NDArray[np.floating]
    """Lignin loss rate from the aboveground structural pool [kg lignin C m^-2]"""
    woody_lignin: NDArray[np.floating]
    """Lignin loss rate from the woody pool [kg lignin C m^-2]"""
    below_structural_lignin: NDArray[np.floating]
    """Lignin loss rate from the belowground structural pool [kg lignin C m^-2]"""

    N_mineralisation_rate: NDArray[np.floating]
    """Total nitrogen mineralisation rate from all litter pools [kg N m^-3 day^-1]"""
    P_mineralisation_rate: NDArray[np.floating]
    """Total phosphorus mineralisation rate from all litter pools [kg P m^-3 day^-1]"""


def calculate_litter_losses(
    data: Data,
    original_pools: dict[str, NDArray[np.floating]],
    final_pools: dict[str, NDArray[np.floating]],
    litter_inputs: LitterInputs,
    update_interval: float,
    active_microbe_depth: float,
) -> LitterLosses:
    """Calculate the loss of carbon, nitrogen and phosphorus from each litter pool.

    Total mineralisation rates to soil for nitrogen and phosphorus are also calculated.

    Args:
        data: A :class:`~virtual_ecosystem.core.data.Data` instance.
        original_pools: Pool sizes before any litter input and decay [kg C m^-2].
        final_pools: Pool sizes after litter input and decay [kg C m^-2].
        litter_inputs: The inputs to each litter pool [kg C m^-2 day^-1].
        update_interval: The time period over which the litter pools are updated [days].
        active_microbe_depth: The depth at which microbial activity is assumed to cease
            [m].

    Returns:
        A dataclass containing the total losses of each nutrient from each litter pool,
        as well as the total mineralisation rates to the soil for each nutrient.
    """

    # Calculate the loss of carbon from each litter pool
    above_metabolic_carbon = calculate_carbon_pool_loss(
        old_pool_size=original_pools["above_metabolic"],
        final_pool_size=final_pools["above_metabolic"],
        input_rate=litter_inputs.above_metabolic,
        update_interval=update_interval,
    )
    above_structural_carbon = calculate_carbon_pool_loss(
        old_pool_size=original_pools["above_structural"],
        final_pool_size=final_pools["above_structural"],
        input_rate=litter_inputs.above_structural,
        update_interval=update_interval,
    )
    woody_carbon = calculate_carbon_pool_loss(
        old_pool_size=original_pools["woody"],
        final_pool_size=final_pools["woody"],
        input_rate=litter_inputs.woody,
        update_interval=update_interval,
    )
    below_metabolic_carbon = calculate_carbon_pool_loss(
        old_pool_size=original_pools["below_metabolic"],
        final_pool_size=final_pools["below_metabolic"],
        input_rate=litter_inputs.below_metabolic,
        update_interval=update_interval,
    )
    below_structural_carbon = calculate_carbon_pool_loss(
        old_pool_size=original_pools["below_structural"],
        final_pool_size=final_pools["below_structural"],
        input_rate=litter_inputs.below_structural,
        update_interval=update_interval,
    )

    # Calculate the loss of nitrogen from each litter pool
    above_metabolic_nitrogen = (
        above_metabolic_carbon / data["c_n_ratio_above_metabolic"]
    )
    above_structural_nitrogen = (
        above_structural_carbon / data["c_n_ratio_above_structural"]
    )
    woody_nitrogen = woody_carbon / data["c_n_ratio_woody"]
    below_metabolic_nitrogen = (
        below_metabolic_carbon / data["c_n_ratio_below_metabolic"]
    )
    below_structural_nitrogen = (
        below_structural_carbon / data["c_n_ratio_below_structural"]
    )

    # Calculate the loss of phosphorus from each litter pool
    above_metabolic_phosphorus = (
        above_metabolic_carbon / data["c_p_ratio_above_metabolic"]
    )
    above_structural_phosphorus = (
        above_structural_carbon / data["c_p_ratio_above_structural"]
    )
    woody_phosphorus = woody_carbon / data["c_p_ratio_woody"]
    below_metabolic_phosphorus = (
        below_metabolic_carbon / data["c_p_ratio_below_metabolic"]
    )
    below_structural_phosphorus = (
        below_structural_carbon / data["c_p_ratio_below_structural"]
    )

    # Calculate the loss of lignin from the three relevant litter pools
    above_structural_lignin = above_structural_carbon * data["lignin_above_structural"]
    woody_lignin = woody_carbon * data["lignin_woody"]
    below_structural_lignin = below_structural_carbon * data["lignin_below_structural"]

    # Finally, calculate the total mineralisation rates for nitrogen and phosphorus
    N_mineralisation_rate = (
        above_metabolic_nitrogen
        + above_structural_nitrogen
        + woody_nitrogen
        + below_metabolic_nitrogen
        + below_structural_nitrogen
    ) / (update_interval * active_microbe_depth)
    P_mineralisation_rate = (
        above_metabolic_phosphorus
        + above_structural_phosphorus
        + woody_phosphorus
        + below_metabolic_phosphorus
        + below_structural_phosphorus
    ) / (update_interval * active_microbe_depth)

    return LitterLosses(
        above_metabolic_carbon=above_metabolic_carbon,
        above_structural_carbon=above_structural_carbon,
        woody_carbon=woody_carbon,
        below_metabolic_carbon=below_metabolic_carbon,
        below_structural_carbon=below_structural_carbon,
        above_metabolic_nitrogen=above_metabolic_nitrogen,
        above_structural_nitrogen=above_structural_nitrogen,
        woody_nitrogen=woody_nitrogen,
        below_metabolic_nitrogen=below_metabolic_nitrogen,
        below_structural_nitrogen=below_structural_nitrogen,
        above_metabolic_phosphorus=above_metabolic_phosphorus,
        above_structural_phosphorus=above_structural_phosphorus,
        woody_phosphorus=woody_phosphorus,
        below_metabolic_phosphorus=below_metabolic_phosphorus,
        below_structural_phosphorus=below_structural_phosphorus,
        above_structural_lignin=above_structural_lignin,
        woody_lignin=woody_lignin,
        below_structural_lignin=below_structural_lignin,
        N_mineralisation_rate=N_mineralisation_rate,
        P_mineralisation_rate=P_mineralisation_rate,
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

    Returns:
        The total loss of carbon from the pool due to decay [kg C m^-2]
    """

    return old_pool_size + (input_rate * update_interval) - final_pool_size
