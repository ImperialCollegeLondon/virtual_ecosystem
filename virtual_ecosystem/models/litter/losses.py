"""The ``models.litter.losses`` module handles the calculation of the total loss of each
nutrient (carbon, nitrogen and phosphorus) from each litter pool, as well as the total
mineralisation rate to soil of each nutrient.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.litter.inputs import InputChemistries, LitterInputs


@dataclass(frozen=True)
class LitterLosses:
    """The full set losses for the litter pools, as well as the mineralisation rates."""

    above_metabolic_carbon: NDArray[np.floating]
    """Carbon loss from the aboveground metabolic pool [kg C m^-2]"""
    above_structural_carbon: NDArray[np.floating]
    """Carbon loss from the aboveground structural pool [kg C m^-2]"""
    woody_carbon: NDArray[np.floating]
    """Carbon loss from the woody pool [kg C m^-2]"""
    below_metabolic_carbon: NDArray[np.floating]
    """Carbon loss from the belowground metabolic pool [kg C m^-2]"""
    below_structural_carbon: NDArray[np.floating]
    """Carbon loss from the belowground structural pool [kg C m^-2]"""

    above_metabolic_nitrogen: NDArray[np.floating]
    """Nitrogen loss from the aboveground metabolic pool [kg N m^-2]"""
    above_structural_nitrogen: NDArray[np.floating]
    """Nitrogen loss from the aboveground structural pool [kg N m^-2]"""
    woody_nitrogen: NDArray[np.floating]
    """Nitrogen loss from the woody pool [kg N m^-2]"""
    below_metabolic_nitrogen: NDArray[np.floating]
    """Nitrogen loss from the belowground metabolic pool [kg N m^-2]"""
    below_structural_nitrogen: NDArray[np.floating]
    """Nitrogen loss from the belowground structural pool [kg N m^-2]"""

    above_metabolic_phosphorus: NDArray[np.floating]
    """Phosphorus loss from the aboveground metabolic pool [kg P m^-2]"""
    above_structural_phosphorus: NDArray[np.floating]
    """Phosphorus loss from the aboveground structural pool [kg P m^-2]"""
    woody_phosphorus: NDArray[np.floating]
    """Phosphorus loss from the woody pool [kg P m^-2]"""
    below_metabolic_phosphorus: NDArray[np.floating]
    """Phosphorus loss from the belowground metabolic pool [kg P m^-2]"""
    below_structural_phosphorus: NDArray[np.floating]
    """Phosphorus loss from the belowground structural pool [kg P m^-2]"""

    above_structural_lignin: NDArray[np.floating]
    """Lignin loss from the aboveground structural pool [kg lignin C m^-2]"""
    woody_lignin: NDArray[np.floating]
    """Lignin loss from the woody pool [kg lignin C m^-2]"""
    below_structural_lignin: NDArray[np.floating]
    """Lignin loss from the belowground structural pool [kg lignin C m^-2]"""

    N_mineralisation_rate: NDArray[np.floating]
    """Total nitrogen mineralisation rate from all litter pools [kg N m^-3 day^-1]"""
    P_mineralisation_rate: NDArray[np.floating]
    """Total phosphorus mineralisation rate from all litter pools [kg P m^-3 day^-1]"""


def calculate_litter_losses(
    data: Data,
    original_pools: dict[str, NDArray[np.floating]],
    final_pools: dict[str, NDArray[np.floating]],
    litter_inputs: LitterInputs,
    input_chemistries: InputChemistries,
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
        input_chemistries: The chemical compositions of the inputs to each litter pool.
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
    above_metabolic_nitrogen = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["above_metabolic"],
        carbon_loss=above_metabolic_carbon,
        input_rate=litter_inputs.above_metabolic,
        initial_carbon_nutrient_ratio=data["c_n_ratio_above_metabolic"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.above_metabolic_nitrogen,
        update_interval=update_interval,
    )
    above_structural_nitrogen = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["above_structural"],
        carbon_loss=above_structural_carbon,
        input_rate=litter_inputs.above_structural,
        initial_carbon_nutrient_ratio=data["c_n_ratio_above_structural"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.above_structural_nitrogen,
        update_interval=update_interval,
    )
    woody_nitrogen = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["woody"],
        carbon_loss=woody_carbon,
        input_rate=litter_inputs.woody,
        initial_carbon_nutrient_ratio=data["c_n_ratio_woody"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.woody_nitrogen,
        update_interval=update_interval,
    )
    below_metabolic_nitrogen = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["below_metabolic"],
        carbon_loss=below_metabolic_carbon,
        input_rate=litter_inputs.below_metabolic,
        initial_carbon_nutrient_ratio=data["c_n_ratio_below_metabolic"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.below_metabolic_nitrogen,
        update_interval=update_interval,
    )
    below_structural_nitrogen = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["below_structural"],
        carbon_loss=below_structural_carbon,
        input_rate=litter_inputs.below_structural,
        initial_carbon_nutrient_ratio=data["c_n_ratio_below_structural"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.below_structural_nitrogen,
        update_interval=update_interval,
    )

    # Calculate the loss of nitrogen from each litter pool
    above_metabolic_phosphorus = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["above_metabolic"],
        carbon_loss=above_metabolic_carbon,
        input_rate=litter_inputs.above_metabolic,
        initial_carbon_nutrient_ratio=data["c_p_ratio_above_metabolic"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.above_metabolic_phosphorus,
        update_interval=update_interval,
    )
    above_structural_phosphorus = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["above_structural"],
        carbon_loss=above_structural_carbon,
        input_rate=litter_inputs.above_structural,
        initial_carbon_nutrient_ratio=data["c_p_ratio_above_structural"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.above_structural_phosphorus,
        update_interval=update_interval,
    )
    woody_phosphorus = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["woody"],
        carbon_loss=woody_carbon,
        input_rate=litter_inputs.woody,
        initial_carbon_nutrient_ratio=data["c_p_ratio_woody"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.woody_phosphorus,
        update_interval=update_interval,
    )
    below_metabolic_phosphorus = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["below_metabolic"],
        carbon_loss=below_metabolic_carbon,
        input_rate=litter_inputs.below_metabolic,
        initial_carbon_nutrient_ratio=data["c_p_ratio_below_metabolic"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.below_metabolic_phosphorus,
        update_interval=update_interval,
    )
    below_structural_phosphorus = calculate_nutrient_pool_loss(
        initial_pool_size=original_pools["below_structural"],
        carbon_loss=below_structural_carbon,
        input_rate=litter_inputs.below_structural,
        initial_carbon_nutrient_ratio=data["c_p_ratio_below_structural"].to_numpy(),
        input_carbon_nutrient_ratio=input_chemistries.below_structural_phosphorus,
        update_interval=update_interval,
    )

    # Calculate the loss of lignin from the three relevant litter pools
    above_structural_lignin = calculate_lignin_pool_loss(
        initial_pool_size=original_pools["above_structural"],
        carbon_loss=above_structural_carbon,
        input_rate=litter_inputs.above_structural,
        initial_lignin_proportion=data["lignin_above_structural"].to_numpy(),
        input_lignin_proportion=input_chemistries.above_structural_lignin,
        update_interval=update_interval,
    )
    woody_lignin = calculate_lignin_pool_loss(
        initial_pool_size=original_pools["woody"],
        carbon_loss=woody_carbon,
        input_rate=litter_inputs.woody,
        initial_lignin_proportion=data["lignin_woody"].to_numpy(),
        input_lignin_proportion=input_chemistries.woody_lignin,
        update_interval=update_interval,
    )
    below_structural_lignin = calculate_lignin_pool_loss(
        initial_pool_size=original_pools["below_structural"],
        carbon_loss=below_structural_carbon,
        input_rate=litter_inputs.below_structural,
        initial_lignin_proportion=data["lignin_below_structural"].to_numpy(),
        input_lignin_proportion=input_chemistries.below_structural_lignin,
        update_interval=update_interval,
    )

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


def calculate_nutrient_pool_loss(
    initial_pool_size: NDArray[np.floating],
    carbon_loss: NDArray[np.floating],
    input_rate: NDArray[np.floating],
    initial_carbon_nutrient_ratio: NDArray[np.floating],
    input_carbon_nutrient_ratio: NDArray[np.floating],
    update_interval: float,
) -> NDArray[np.floating]:
    """Calculate the total nutrient loss from a specific litter pool.

    The change in the litter pool carbon content is found using an analytic solution,
    but we don't have a comparable solution for the litter chemistries. Instead we make
    the assumption that older material will preferentially break down, so the initial
    pool stoichiometry can be used to calculate the approximate rate of nutrient loss.
    However, applying this assumption in the case where the total loss of carbon is
    larger than the initial pool size would break stoichiometric balance. In this case,
    we assume that the entire initial pool has decayed and the additional carbon loss
    comes from the input. The nutrient losses are then calculated based on this assumed
    split.

    Args:
        initial_pool_size: The size of the litter pool before the update [kg C m^-2].
        carbon_loss: The total loss of carbon from the pool over the decay period
            [kg C m^-2].
        input_rate: The rate of carbon input to the litter pool [kg C m^-2 day^-1].
        initial_carbon_nutrient_ratio: The carbon to nutrient ratio of the litter pool
            before the update [unitless]
        input_carbon_nutrient_ratio: The carbon to nutrient ratio of the input to the
            litter pool [unitless]
        update_interval: The time period over which the litter pools are updated [days].

    Returns:
        The total loss of nutrient from the pool due to decay [kg nutrient m^-2]
    """

    # Find the fraction of the initial pool that has decayed, and the fraction of input
    # that decays (if the initial pool isn't sufficient)
    fraction_of_initial_pool_decayed = np.where(
        carbon_loss > initial_pool_size, 1, carbon_loss / initial_pool_size
    )
    fraction_of_new_input_decayed = np.divide(
        carbon_loss - initial_pool_size,
        input_rate * update_interval,
        out=np.zeros_like(carbon_loss, dtype=float),
        where=(carbon_loss > initial_pool_size) & (input_rate != 0),
    )

    # Then calculate the amount of nutrient there initially and added due to input
    initial_nutrient = initial_pool_size / initial_carbon_nutrient_ratio
    input_nutrient = input_rate * update_interval / input_carbon_nutrient_ratio

    return (
        fraction_of_initial_pool_decayed * initial_nutrient
        + fraction_of_new_input_decayed * input_nutrient
    )


def calculate_lignin_pool_loss(
    initial_pool_size: NDArray[np.floating],
    carbon_loss: NDArray[np.floating],
    input_rate: NDArray[np.floating],
    initial_lignin_proportion: NDArray[np.floating],
    input_lignin_proportion: NDArray[np.floating],
    update_interval: float,
) -> NDArray[np.floating]:
    """Calculate the total lignin loss from a specific litter pool.

    The change in the litter pool carbon content is found using an analytic solution,
    but we don't have a comparable solution for the litter chemistries. Instead we make
    the assumption that older material will preferentially break down, so the initial
    pool lignin proportion can be used to calculate the approximate rate of lignin loss.
    However, applying this assumption in the case where the total loss of carbon is
    larger than the initial pool size would lead to spontaneous loss or creation of
    lignin. In this case, we assume that the entire initial pool has decayed and the
    additional carbon loss comes from the input. The lignin losses are then calculated
    based on this assumed split.

    Args:
        initial_pool_size: The size of the litter pool before the update [kg C m^-2].
        carbon_loss: The total loss of carbon from the pool over the decay period
            [kg C m^-2].
        input_rate: The rate of carbon input to the litter pool [kg C m^-2 day^-1].
        initial_lignin_proportion: The lignin proportion of the litter pool before the
            update [kg lignin C (kg C)^-1]
        input_lignin_proportion: The lignin proportion of the input to the litter
            pool [kg lignin C (kg C)^-1]
        update_interval: The time period over which the litter pools are updated [days].

    Returns:
        The total loss of lignin from the pool due to decay [kg lignin C m^-2]
    """

    # Find the fraction of the initial pool that has decayed, and the fraction of input
    # that decays (if the initial pool isn't sufficient)
    fraction_of_initial_pool_decayed = np.where(
        carbon_loss > initial_pool_size, 1, carbon_loss / initial_pool_size
    )
    fraction_of_new_input_decayed = np.divide(
        carbon_loss - initial_pool_size,
        input_rate * update_interval,
        out=np.zeros_like(carbon_loss, dtype=float),
        where=(carbon_loss > initial_pool_size) & (input_rate != 0),
    )

    # Then calculate the amount of nutrient there initially and added due to input
    initial_lignin = initial_pool_size * initial_lignin_proportion
    input_lignin = input_rate * update_interval * input_lignin_proportion

    return (
        fraction_of_initial_pool_decayed * initial_lignin
        + fraction_of_new_input_decayed * input_lignin
    )
