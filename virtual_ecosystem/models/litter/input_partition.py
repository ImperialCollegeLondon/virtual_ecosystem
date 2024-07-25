"""The ``models.litter.input_partition`` module handles the partitioning of dead plant
and animal matter into the various pools of the litter model.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.litter.constants import LitterConsts

# TODO - It makes sense for the animal pools to be handled here, but need to think about
# how the partition works with the plant partition, Animals do not contain lignin, so if
# I used the standard function on animal carcasses and excrement the maximum amount
# (85%) will end up in the metabolic pool, which I think is basically fine, with bones
# not being explicitly modelled I think this is fine. This will have to change once
# bones are included.


def calculate_metabolic_proportions_of_input(
    leaf_turnover_lignin_proportion: NDArray[np.float32],
    reproduct_turnover_lignin_proportion: NDArray[np.float32],
    root_turnover_lignin_proportion: NDArray[np.float32],
    leaf_turnover_c_n_ratio: NDArray[np.float32],
    reproduct_turnover_c_n_ratio: NDArray[np.float32],
    root_turnover_c_n_ratio: NDArray[np.float32],
    constants: LitterConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate the proportion of each input type that flows to the metabolic pool.

    This function is used for roots, leaves and reproductive tissue, but not deadwood
    because everything goes into a single woody litter pool. It is not used for animal
    inputs either as they all flow into just the metabolic pool.

    Args:
        leaf_turnover_lignin_proportion: Proportion of carbon in turned over leaves that
            is lignin [kg lignin kg C^-1]
        reproduct_turnover_lignin_proportion: Proportion of carbon in turned over
            reproductive tissues that is lignin [kg lignin kg C^-1]
        root_turnover_lignin_proportion: Proportion of carbon in turned over roots that
            is lignin [kg lignin kg C^-1]
        leaf_turnover_c_n_ratio: Carbon:nitrogen ratio of turned over leaves [unitless]
        reproduct_turnover_c_n_ratio: Carbon:nitrogen ratio of turned over reproductive
            tissues [unitless]
        root_turnover_c_n_ratio: Carbon:nitrogen ratio of turned over roots [unitless]
        constants: Set of constants for the litter model.

    Returns:
        A dictionary containing the proportion of the input that goes to the relevant
        metabolic pool. This is for three input types: leaves, reproductive tissues and
        roots [unitless]
    """

    # Calculate split of each input biomass type
    leaves_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=leaf_turnover_lignin_proportion,
        carbon_nitrogen_ratio=leaf_turnover_c_n_ratio,
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity=constants.structural_metabolic_split_sensitivity,
    )
    repoduct_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=reproduct_turnover_lignin_proportion,
        carbon_nitrogen_ratio=reproduct_turnover_c_n_ratio,
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity=constants.structural_metabolic_split_sensitivity,
    )
    roots_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=root_turnover_lignin_proportion,
        carbon_nitrogen_ratio=root_turnover_c_n_ratio,
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity=constants.structural_metabolic_split_sensitivity,
    )

    return {
        "leaves": leaves_metabolic_split,
        "reproductive": repoduct_metabolic_split,
        "roots": roots_metabolic_split,
    }


def partion_plant_inputs_between_pools(
    deadwood_production: NDArray[np.float32],
    leaf_turnover: NDArray[np.float32],
    reproduct_turnover: NDArray[np.float32],
    root_turnover: NDArray[np.float32],
    metabolic_splits: dict[str, NDArray[np.float32]],
):
    """Function to partition input biomass between the various litter pools.

    All deadwood is added to the woody litter pool. Reproductive biomass (fruits and
    flowers) and leaves are split between the above ground metabolic and structural
    pools based on lignin concentration and carbon nitrogen ratios. Root biomass is
    split between between the below ground metabolic and structural pools based on
    lignin concentration and carbon nitrogen ratios.

    Args:
        deadwood_production: Amount of dead wood produced [kg C m^-2]
        leaf_turnover: Amount of leaf turnover [kg C m^-2]
        reproduct_turnover: Turnover of plant reproductive tissues (i.e. fruits and
            flowers) [kg C m^-2]
        root_turnover: Turnover of roots (coarse and fine) turnover [kg C m^-2]
        metabolic_splits: Dictionary containing the proportion of each input that goes
            to the relevant metabolic pool. This is for three input types: leaves,
            reproductive tissues and roots [unitless]

    Returns:
        A dictionary containing the biomass flow into each of the five litter pools
        (woody, above ground metabolic, above ground structural, below ground metabolic
        and below ground structural)
    """

    # Calculate input to each of the five litter pools
    woody_input = deadwood_production
    above_ground_metabolic_input = (
        metabolic_splits["leaves"] * leaf_turnover
        + metabolic_splits["reproductive"] * reproduct_turnover
    )
    above_ground_strutural_input = (
        (1 - metabolic_splits["leaves"]) * leaf_turnover
        + (1 - metabolic_splits["reproductive"]) * reproduct_turnover
    )  # fmt: off
    below_ground_metabolic_input = metabolic_splits["roots"] * root_turnover
    below_ground_structural_input = (1 - metabolic_splits["roots"]) * root_turnover

    return {
        "woody": woody_input,
        "above_ground_metabolic": above_ground_metabolic_input,
        "above_ground_structural": above_ground_strutural_input,
        "below_ground_metabolic": below_ground_metabolic_input,
        "below_ground_structural": below_ground_structural_input,
    }


def split_pool_into_metabolic_and_structural_litter(
    lignin_proportion: NDArray[np.float32],
    carbon_nitrogen_ratio: NDArray[np.float32],
    max_metabolic_fraction: float,
    split_sensitivity: float,
) -> NDArray[np.float32]:
    """Calculate the split of input biomass between metabolic and structural pools.

    This division depends on the lignin and nitrogen content of the input biomass, the
    functional form is taken from :cite:t:`parton_dynamics_1988`.

    TODO - This can almost certainly be extended to include phosphorus co-limitation.

    Args:
        lignin_proportion: Proportion of input biomass carbon that is lignin [kg lignin
            kg C^-1]
        carbon_nitrogen_ratio: Ratio of carbon to nitrogen for the input biomass
            [unitless]
        max_metabolic_fraction: Fraction of pool that becomes metabolic litter for the
            easiest to breakdown case, i.e. no lignin, ample nitrogen [unitless]
        split_sensitivity: Sets how rapidly the split changes in response to changing
            lignin and nitrogen contents [unitless]

    Raises:
        ValueError: If any of the metabolic fractions drop below zero, or if any
            structural fraction is less than the lignin proportion (which would push the
            lignin proportion of the structural litter input above 100%).

    Returns:
        The fraction of the biomass that goes to the metabolic pool [unitless]
    """

    metabolic_fraction = max_metabolic_fraction - split_sensitivity * (
        lignin_proportion * carbon_nitrogen_ratio
    )

    if np.any(metabolic_fraction < 0.0):
        to_raise = ValueError(
            "Fraction of input biomass going to metabolic pool has dropped below zero!"
        )
        LOGGER.error(to_raise)
        raise to_raise
    elif np.any(1 - metabolic_fraction < lignin_proportion):
        to_raise = ValueError(
            "Fraction of input biomass going to structural biomass is less than the "
            "lignin fraction!"
        )
        LOGGER.error(to_raise)
        raise to_raise
    else:
        return metabolic_fraction


def calculate_litter_input_lignin_concentrations(
    deadwood_lignin_proportion: NDArray[np.float32],
    root_turnover_lignin_proportion: NDArray[np.float32],
    leaf_turnover_lignin_proportion: NDArray[np.float32],
    reproduct_turnover_lignin_proportion: NDArray[np.float32],
    root_turnover: NDArray[np.float32],
    leaf_turnover: NDArray[np.float32],
    reproduct_turnover: NDArray[np.float32],
    plant_input_below_struct: NDArray[np.float32],
    plant_input_above_struct: NDArray[np.float32],
) -> dict[str, NDArray[np.float32]]:
    """Calculate the concentration of lignin for each plant biomass to litter pool flow.

    By definition the metabolic litter pools do not contain lignin, so all input lignin
    flows to the structural and woody pools. As the input biomass gets split between
    pools, the lignin concentration of the input to the structural pools will be higher
    than it was in the input biomass.

    For the woody litter there's no structural-metabolic split so the lignin
    concentration of the litter input is the same as that of the dead wood production.
    For the below ground structural litter, the total lignin content of root input must
    be found, this is then converted back into a concentration relative to the input
    into the below structural litter pool. For the above ground structural litter pool,
    the same approach is taken with the combined total lignin content of the leaf and
    reproductive matter inputs being found, and then converted to a back into a
    concentration.

    Args:
        deadwood_lignin_proportion: Proportion of carbon in dead wood that is lignin [kg
            lignin kg C^-1]
        root_turnover_lignin_proportion: Proportion of carbon in turned over roots that
            is lignin [kg lignin kg C^-1]
        leaf_turnover_lignin_proportion: Proportion of carbon in turned over leaves that
            is lignin [kg lignin kg C^-1]
        reproduct_turnover_lignin_proportion: Proportion of carbon in turned over
            reproductive tissues that is lignin [kg lignin kg C^-1]
        root_turnover: Turnover of roots (coarse and fine) turnover [kg C m^-2]
        leaf_turnover: Amount of leaf turnover [kg C m^-2]
        reproduct_turnover: Turnover of plant reproductive tissues (i.e. fruits and
            flowers) [kg C m^-2]
        plant_input_below_struct: Plant input to below ground structural litter pool [kg
            C m^-2]
        plant_input_above_struct: Plant input to above ground structural litter pool [kg
            C m^-2]

    Returns:
        Dictionary containing the lignin concentration of the input to each of the three
        lignin containing litter pools (woody, above and below ground structural) [kg
        lignin kg C^-1]
    """

    lignin_proportion_woody = deadwood_lignin_proportion

    lignin_proportion_below_structural = (
        root_turnover_lignin_proportion * root_turnover / plant_input_below_struct
    )

    lignin_proportion_above_structural = (
        (leaf_turnover_lignin_proportion * leaf_turnover)
        + (reproduct_turnover_lignin_proportion * reproduct_turnover)
    ) / plant_input_above_struct

    return {
        "woody": lignin_proportion_woody,
        "below_structural": lignin_proportion_below_structural,
        "above_structural": lignin_proportion_above_structural,
    }


def calculate_litter_input_nitrogen_ratios(
    deadwood_c_n_ratio: NDArray[np.float32],
    root_turnover_c_n_ratio: NDArray[np.float32],
    leaf_turnover_c_n_ratio: NDArray[np.float32],
    reproduct_turnover_c_n_ratio: NDArray[np.float32],
    leaf_turnover: NDArray[np.float32],
    reproduct_turnover: NDArray[np.float32],
    metabolic_splits: dict[str, NDArray[np.float32]],
    struct_to_meta_nitrogen_ratio: float,
) -> dict[str, NDArray[np.float32]]:
    """Calculate the carbon:nitrogen ratio for each plant biomass to litter pool flow.

    The ratio for the input to the woody litter pool just matches the ratio of the
    deadwood input. For the below ground pools, the ratios of the flows from root
    turnover into the metabolic and structural pools is calculated. A similar approach
    is taken for the above ground metabolic and structural pools, but here a weighted
    average of the two contributions to each pool (leaf and reproductive tissue
    turnover) must be taken.

    Args:
        deadwood_c_n_ratio: Carbon:nitrogen ratio of deadwood [unitless]
        root_turnover_c_n_ratio: Carbon:nitrogen ratio of turned over roots [unitless]
        leaf_turnover_c_n_ratio: Carbon:nitrogen ratio of turned over leaves [unitless]
        reproduct_turnover_c_n_ratio: Carbon:nitrogen ratio of turned over reproductive
            tissues [unitless]
        leaf_turnover: Amount of leaf turnover [kg C m^-2]
        reproduct_turnover: Turnover of plant reproductive tissues (i.e. fruits and
            flowers) [kg C m^-2]
        metabolic_splits: Dictionary containing the proportion of each input that goes
            to the relevant metabolic pool. This is for three input types: leaves,
            reproductive tissues and roots [unitless]
        struct_to_meta_nitrogen_ratio: Ratio of the carbon:nitrogen ratios of structural
            vs metabolic litter pools [unitless]

    Returns:
        Dictionary containing the C:N ratios of the input to each of the pools
        [unitless]
    """

    # Calculate c_n_ratio split for each (non-wood) input biomass type
    root_c_n_ratio_meta, root_c_n_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=root_turnover_c_n_ratio,
            metabolic_split=metabolic_splits["roots"],
            struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
        )
    )
    leaf_c_n_ratio_meta, leaf_c_n_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=leaf_turnover_c_n_ratio,
            metabolic_split=metabolic_splits["leaves"],
            struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
        )
    )
    reprod_c_n_ratio_meta, reprod_c_n_ratio_struct = (
        calculate_nutrient_split_between_litter_pools(
            input_c_nut_ratio=reproduct_turnover_c_n_ratio,
            metabolic_split=metabolic_splits["reproductive"],
            struct_to_meta_nutrient_ratio=struct_to_meta_nitrogen_ratio,
        )
    )

    c_n_ratio_below_metabolic = root_c_n_ratio_meta
    c_n_ratio_below_structural = root_c_n_ratio_struct
    c_n_ratio_woody = deadwood_c_n_ratio
    # Inputs with multiple sources have to be weighted
    c_n_ratio_above_metabolic = np.divide(
        leaf_c_n_ratio_meta * leaf_turnover * metabolic_splits["leaves"]
        + reprod_c_n_ratio_meta * reproduct_turnover * metabolic_splits["reproductive"],
        leaf_turnover * metabolic_splits["leaves"]
        + reproduct_turnover * metabolic_splits["reproductive"],
    )
    c_n_ratio_above_structural = np.divide(
        leaf_c_n_ratio_struct * leaf_turnover * (1 - metabolic_splits["leaves"])
        + reprod_c_n_ratio_struct
        * reproduct_turnover
        * (1 - metabolic_splits["reproductive"]),
        leaf_turnover * (1 - metabolic_splits["leaves"])
        + reproduct_turnover * (1 - metabolic_splits["reproductive"]),
    )

    return {
        "woody": c_n_ratio_woody,
        "below_metabolic": c_n_ratio_below_metabolic,
        "below_structural": c_n_ratio_below_structural,
        "above_metabolic": c_n_ratio_above_metabolic,
        "above_structural": c_n_ratio_above_structural,
    }


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
        struct_to_meta_nutrient_ratio: Ratio of the carbon:nutrient ratios of structural
            vs metabolic litter pools [unitless]

    Returns:
        A tuple containing the C:N ratio of the organic matter input to the metabolic
        and structural litter pools, in that order.
    """

    c_n_ratio_meta_input = np.divide(
        input_c_nut_ratio,
        metabolic_split + struct_to_meta_nutrient_ratio * (1 - metabolic_split),
    )

    c_n_ratio_struct_input = struct_to_meta_nutrient_ratio * c_n_ratio_meta_input

    return (c_n_ratio_meta_input, c_n_ratio_struct_input)
