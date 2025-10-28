"""The ``models.litter.inputs`` module handles the partitioning of plant matter into the
various pools of the litter model. This plant matter comes from both natural tissue
death as well as from mechanical inefficiencies in herbivory.
"""  # noqa: D205

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.litter.model_config import LitterConstants


@dataclass(frozen=True)
class LitterInputs:
    """The full set input flows to the litter model."""

    leaf_mass: NDArray[np.floating]
    """Total leaf input rate to litter [kg C m^-2 day^-1]"""
    root_mass: NDArray[np.floating]
    """Total root input rate to litter [kg C m^-2 day^-1]"""
    deadwood_mass: NDArray[np.floating]
    """Total deadwood input rate to litter [kg C m^-2 day^-1]"""
    reprod_mass: NDArray[np.floating]
    """Total plant reproductive tissue input rate to litter [kg C m^-2 day^-1]"""

    leaf_lignin: NDArray[np.floating]
    """Lignin proportion of leaf input [kg lignin C (kg C)^-1]"""
    root_lignin: NDArray[np.floating]
    """Lignin proportion of root input [kg lignin C (kg C)^-1]"""
    stem_lignin: NDArray[np.floating]
    """Lignin proportion of deadwood input [kg lignin C (kg C)^-1]"""
    reprod_lignin: NDArray[np.floating]
    """Lignin proportion of reproductive tissue input [kg lignin C (kg C)^-1]"""

    leaf_nitrogen: NDArray[np.floating]
    """Carbon nitrogen ratio of leaf input [unitless]"""
    root_nitrogen: NDArray[np.floating]
    """Carbon nitrogen ratio of root input [unitless]"""
    deadwood_nitrogen: NDArray[np.floating]
    """Carbon nitrogen ratio of deadwood input [unitless]"""
    reprod_nitrogen: NDArray[np.floating]
    """Carbon nitrogen ratio of reproductive tissue input [unitless]"""

    leaf_phosphorus: NDArray[np.floating]
    """Carbon phosphorus ratio of leaf input [unitless]"""
    root_phosphorus: NDArray[np.floating]
    """Carbon phosphorus ratio of root input [unitless]"""
    deadwood_phosphorus: NDArray[np.floating]
    """Carbon phosphorus ratio of deadwood input [unitless]"""
    reprod_phosphorus: NDArray[np.floating]
    """Carbon phosphorus ratio of reproductive tissue input [unitless]"""

    leaves_meta_split: NDArray[np.floating]
    """Fraction of leaf input that goes to metabolic litter [unitless]"""
    reproduct_meta_split: NDArray[np.floating]
    """Fraction of leaf input that goes to metabolic litter [unitless]"""
    roots_meta_split: NDArray[np.floating]
    """Fraction of leaf input that goes to metabolic litter [unitless]"""

    woody: NDArray[np.floating]
    """Total input rate to the woody litter pool [kg C m^-2 day^-1]"""
    above_metabolic: NDArray[np.floating]
    """Total input rate to the above ground metabolic litter pool [kg C m^-2 day^-1]"""
    above_structural: NDArray[np.floating]
    """Total input rate to the above ground structural litter pool [kg C m^-2 day^-1]"""
    below_metabolic: NDArray[np.floating]
    """Total input rate to the below ground metabolic litter pool [kg C m^-2 day^-1]"""
    below_structural: NDArray[np.floating]
    """Total input rate to the below ground structural litter pool [kg C m^-2 day^-1]"""

    @classmethod
    def create_from_data(
        cls, data: Data, constants: LitterConstants, update_interval: float
    ) -> LitterInputs:
        """Factory method to populate the various litter input flows.

        This method first combines the two different input streams for dead plant matter
        (plant tissue death and herbivory waste) to find the total input of each plant
        biomass type. This is then used to find the split between metabolic and
        structural litter pools for each plant matter class (expect deadwood). Finally,
        the total rate of flow to each litter pool is calculated.

        Args:
            data: The `Data` object to be used to populate the litter input details.
            constants: Set of constants for the litter model.
            update_interval: The length of time over which the input is being added over
                [days]

        Returns:
            An LitterInputs instance containing the total input of each plant biomass
            type, the proportion of the input that goes to the relevant metabolic pool
            for each input type (expect deadwood) and the total input into each litter
            pool.
        """

        # Find the total input for each plant matter type
        total_input = combine_input_sources(data, update_interval=update_interval)

        # Find the plant inputs to each of the litter pools
        metabolic_splits = calculate_metabolic_proportions_of_input(
            total_input=total_input, constants=constants
        )

        plant_inputs = partion_plant_inputs_between_pools(
            total_input=total_input,
            metabolic_splits=metabolic_splits,
        )

        return LitterInputs(**metabolic_splits, **plant_inputs, **total_input)


def combine_input_sources(
    data: Data, update_interval: float
) -> dict[str, NDArray[np.floating]]:
    """Combine the plant death and herbivory inputs into a single total input.

    The total input for each plant matter type (leaves, roots, deadwood,
    reproductive tissue) is returned, the chemical concentration of each of these
    new pools is also calculated.

    This function also converts the plant inputs from total inputs (over the model time
    step), to the input rates needed by the litter model.

    TODO - At the moment there is only leaf input defined so this function doesn't
    really do anything for the other types of plant matter. Once input is defined
    for them this function should be updated to actually do something with them.

    Args:
        data: The `Data` object to be used to populate the litter input streams.
        update_interval: The length of time over which the input is being added over
            [days]

    Returns:
        A dictionary containing the total pool size for each input pools [kg C m^-3], as
        well as the carbon to nitrogen ratios [unitless], carbon to phosphorus ratios
        [unitless] and lignin proportions [kg lignin C (kg C)^-1] of each of these
        pools.
    """

    # Calculate totals for each plant matter type
    leaf_total = (
        data["leaf_turnover"] + data["herbivory_waste_leaf_carbon"]
    ).to_numpy()
    root_total = data["root_turnover"]
    deadwood_total = data["deadwood_production"]
    reprod_total = data["fallen_non_propagule_c_mass"]

    # Calculate lignin concentrations for each combined pool
    leaf_lignin = merge_input_lignin_proportions(
        turnover_mass=data["leaf_turnover"].to_numpy(),
        herbivory_waste_mass=data["herbivory_waste_leaf_carbon"].to_numpy(),
        total_mass=leaf_total,
        turnover_lignin_proportion=data["senesced_leaf_lignin"].to_numpy(),
        herbivory_waste_lignin_proportion=data[
            "herbivory_waste_leaf_lignin"
        ].to_numpy(),
    )
    root_lignin = data["root_lignin"]
    stem_lignin = data["stem_lignin"]
    reprod_lignin = data["plant_reproductive_tissue_lignin"]

    # Calculate leaf nitrogen concentrations for each combined pool
    leaf_nitrogen = average_nutrient_ratios(
        mass_1=data["leaf_turnover"].to_numpy(),
        mass_2=data["herbivory_waste_leaf_carbon"].to_numpy(),
        nutrient_ratio_1=data["leaf_turnover_c_n_ratio"].to_numpy(),
        nutrient_ratio_2=data["herbivory_waste_leaf_nitrogen"].to_numpy(),
    )
    root_nitrogen = data["root_turnover_c_n_ratio"]
    deadwood_nitrogen = data["deadwood_c_n_ratio"]
    reprod_nitrogen = data["plant_reproductive_tissue_turnover_c_n_ratio"]

    # Calculate leaf phosphorus concentrations for each combined pool
    leaf_phosphorus = average_nutrient_ratios(
        mass_1=data["leaf_turnover"].to_numpy(),
        mass_2=data["herbivory_waste_leaf_carbon"].to_numpy(),
        nutrient_ratio_1=data["leaf_turnover_c_p_ratio"].to_numpy(),
        nutrient_ratio_2=data["herbivory_waste_leaf_phosphorus"].to_numpy(),
    )
    root_phosphorus = data["root_turnover_c_p_ratio"]
    deadwood_phosphorus = data["deadwood_c_p_ratio"]
    reprod_phosphorus = data["plant_reproductive_tissue_turnover_c_p_ratio"]

    return {
        "leaf_mass": leaf_total / update_interval,
        "root_mass": root_total.to_numpy() / update_interval,
        "deadwood_mass": deadwood_total.to_numpy() / update_interval,
        "reprod_mass": reprod_total.to_numpy() / update_interval,
        "leaf_lignin": leaf_lignin,
        "root_lignin": root_lignin.to_numpy(),
        "stem_lignin": stem_lignin.to_numpy(),
        "reprod_lignin": reprod_lignin.to_numpy(),
        "leaf_nitrogen": leaf_nitrogen,
        "root_nitrogen": root_nitrogen.to_numpy(),
        "deadwood_nitrogen": deadwood_nitrogen.to_numpy(),
        "reprod_nitrogen": reprod_nitrogen.to_numpy(),
        "leaf_phosphorus": leaf_phosphorus,
        "root_phosphorus": root_phosphorus.to_numpy(),
        "deadwood_phosphorus": deadwood_phosphorus.to_numpy(),
        "reprod_phosphorus": reprod_phosphorus.to_numpy(),
    }


def calculate_metabolic_proportions_of_input(
    total_input: dict[str, NDArray[np.floating]], constants: LitterConstants
) -> dict[str, NDArray[np.floating]]:
    """Calculate the proportion of each input type that flows to the metabolic pool.

    This function is used for roots, leaves and reproductive tissue, but not deadwood
    because everything goes into a single woody litter pool. It is not used for animal
    inputs either as they all flow into just the metabolic pool.

    Args:
        total_input: The total pool size for each input pools [kg C m^-3], as
            well as the carbon to nitrogen ratios [unitless], carbon to phosphorus
            ratios [unitless] and lignin proportions [kg lignin C (kg C)^-1] of each of
            these pools.
        constants: Set of constants for the litter model.

    Returns:
        A dictionary containing the proportion of the input that goes to the relevant
        metabolic pool. This is for three input types: leaves, reproductive tissues and
        roots [unitless]
    """

    # Calculate split of each input biomass type

    leaves_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=total_input["leaf_lignin"],
        carbon_nitrogen_ratio=total_input["leaf_nitrogen"],
        carbon_phosphorus_ratio=total_input["leaf_phosphorus"],
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
    )

    repoduct_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=total_input["reprod_lignin"],
        carbon_nitrogen_ratio=total_input["reprod_nitrogen"],
        carbon_phosphorus_ratio=total_input["reprod_phosphorus"],
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
    )

    roots_metabolic_split = split_pool_into_metabolic_and_structural_litter(
        lignin_proportion=total_input["root_lignin"],
        carbon_nitrogen_ratio=total_input["root_nitrogen"],
        carbon_phosphorus_ratio=total_input["root_phosphorus"],
        max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
        split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
        split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
    )

    return {
        "leaves_meta_split": leaves_metabolic_split,
        "reproduct_meta_split": repoduct_metabolic_split,
        "roots_meta_split": roots_metabolic_split,
    }


def partion_plant_inputs_between_pools(
    total_input: dict[str, NDArray[np.floating]],
    metabolic_splits: dict[str, NDArray[np.floating]],
):
    """Function to partition input biomass between the various litter pools.

    All deadwood is added to the woody litter pool. Reproductive biomass (fruits and
    flowers) and leaves are split between the above ground metabolic and structural
    pools based on lignin concentration and carbon nitrogen ratios. Root biomass is
    split between the below ground metabolic and structural pools based on lignin
    concentration and carbon nitrogen ratios.

    Args:
        total_input: The the total pool size for each input pools [kg C m^-3], as
            well as the carbon to nitrogen ratios [unitless], carbon to phosphorus
            ratios [unitless] and lignin proportions [kg lignin C (kg C)^-1] of each of
            these pools.
        metabolic_splits: Dictionary containing the proportion of each input that
            goes to the relevant metabolic pool. This is for three input types:
            leaves, reproductive tissues and roots [unitless]

    Returns:
        A dictionary containing the rate of biomass flow into each of the five litter
        pools (woody, above ground metabolic, above ground structural, below ground
        metabolic and below ground structural) [kg C m^-2 day^-1]
    """

    # Calculate input to each of the five litter pools
    woody_input = total_input["deadwood_mass"]
    above_ground_metabolic_input = (
        metabolic_splits["leaves_meta_split"] * total_input["leaf_mass"]
        + metabolic_splits["reproduct_meta_split"] * total_input["reprod_mass"]
    )
    above_ground_strutural_input = (
        1 - metabolic_splits["leaves_meta_split"]
    ) * total_input["leaf_mass"] + (
        1 - metabolic_splits["reproduct_meta_split"]
    ) * total_input["reprod_mass"]
    below_ground_metabolic_input = (
        metabolic_splits["roots_meta_split"] * total_input["root_mass"]
    )
    below_ground_structural_input = (
        1 - metabolic_splits["roots_meta_split"]
    ) * total_input["root_mass"]

    return {
        "woody": woody_input,
        "above_metabolic": above_ground_metabolic_input,
        "above_structural": above_ground_strutural_input,
        "below_metabolic": below_ground_metabolic_input,
        "below_structural": below_ground_structural_input,
    }


def split_pool_into_metabolic_and_structural_litter(
    lignin_proportion: NDArray[np.floating],
    carbon_nitrogen_ratio: NDArray[np.floating],
    carbon_phosphorus_ratio: NDArray[np.floating],
    max_metabolic_fraction: float,
    split_sensitivity_nitrogen: float,
    split_sensitivity_phosphorus: float,
) -> NDArray[np.floating]:
    """Calculate the split of input biomass between metabolic and structural pools.

    This division depends on the lignin and nitrogen content of the input biomass, the
    functional form is taken from :cite:t:`parton_dynamics_1988`.

    Args:
        lignin_proportion: Proportion of input biomass carbon that is lignin
            [kg lignin C (kg C)^-1]
        carbon_nitrogen_ratio: Ratio of carbon to nitrogen for the input biomass
            [unitless]
        carbon_phosphorus_ratio: Ratio of carbon to phosphorus for the input biomass
            [unitless]
        max_metabolic_fraction: Fraction of pool that becomes metabolic litter for the
            easiest to breakdown case, i.e. no lignin, ample nitrogen [unitless]
        split_sensitivity_nitrogen: Sets how rapidly the split changes in response to
            changing lignin and nitrogen contents [unitless]
        split_sensitivity_phosphorus: Sets how rapidly the split changes in response to
            changing lignin and phosphorus contents [unitless]

    Raises:
        ValueError: If any of the metabolic fractions drop below zero, or if any
            structural fraction is less than the lignin proportion (which would push the
            lignin proportion of the structural litter input above 100%).

    Returns:
        The fraction of the biomass that goes to the metabolic pool [unitless]
    """

    metabolic_fraction = max_metabolic_fraction - lignin_proportion * (
        split_sensitivity_nitrogen * carbon_nitrogen_ratio
        + split_sensitivity_phosphorus * carbon_phosphorus_ratio
    )

    # This is a naive prevention of negative metabolic fraction rates.
    # TODO: full solution in Issue #1010.
    metabolic_fraction = np.where(metabolic_fraction < 0, 0.0, metabolic_fraction)

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


def merge_input_lignin_proportions(
    turnover_mass: NDArray[np.floating],
    herbivory_waste_mass: NDArray[np.floating],
    total_mass: NDArray[np.floating],
    turnover_lignin_proportion: NDArray[np.floating],
    herbivory_waste_lignin_proportion: NDArray[np.floating],
):
    """Merge the lignin proportions of two input sources to the same litter pool.

    Args:
        turnover_mass: Input mass coming from the natural turnover of plant tissue [kg C
            m^-2]
        herbivory_waste_mass: Input mass coming from the mechanical inefficiencies of
            herbivory [kg C m^-2]
        total_mass: The combined mass of the two input sources [kg C m^-2]
        turnover_lignin_proportion: Proportion of lignin in the input mass from
            natural plant turnover [unitless]
        herbivory_waste_lignin_proportion: Proportion of lignin in the input mass from
            mechanical inefficiencies of herbivory [unitless]

    Returns:
        The proportion of carbon that is lignin carbon in the total mass of the new
        combined input stream [kg lignin C (kg C)^-1]
    """

    return (
        turnover_lignin_proportion * turnover_mass
        + herbivory_waste_lignin_proportion * herbivory_waste_mass
    ) / (total_mass)


def average_nutrient_ratios(
    mass_1: NDArray[np.floating],
    mass_2: NDArray[np.floating],
    nutrient_ratio_1: NDArray[np.floating],
    nutrient_ratio_2: NDArray[np.floating],
):
    """Average carbon to nutrient ratios weighted by their carbon content.

    Args:
        mass_1: Total carbon mass of the first pool/input stream
            [kg C m^-2 or kg C m^-2]
        mass_2: Total carbon mass of the second pool/input stream
            [kg C m^-2 or kg C m^-2]
        nutrient_ratio_1: Carbon to nutrient ratio of the first pool/input stream
            [unitless]
        nutrient_ratio_2: Carbon to nutrient ratio of the second pool/input stream
            [unitless]

    Returns:
        The nutrient ratio of the new combined pool/input stream [unitless]
    """

    return (mass_1 + mass_2) / (
        (mass_1 / nutrient_ratio_1) + (mass_2 / nutrient_ratio_2)
    )


@dataclass(frozen=True)
class InputChemistries:
    """Dataclass containing the chemistry for the input to each litter pool."""

    above_metabolic_nitrogen: NDArray[np.floating]
    """Carbon to nitrogen ratio of input to the aboveground metabolic pool [unitless]"""
    above_structural_nitrogen: NDArray[np.floating]
    """Carbon to nitrogen ratio of input to the aboveground structural pool [unitless].
    """
    woody_nitrogen: NDArray[np.floating]
    """Carbon to nitrogen ratio of input to the woody pool [unitless]"""
    below_metabolic_nitrogen: NDArray[np.floating]
    """Carbon to nitrogen ratio of input to the belowground metabolic pool [unitless]"""
    below_structural_nitrogen: NDArray[np.floating]
    """Carbon to nitrogen ratio of input to the belowground structural pool [unitless]
    """

    above_metabolic_phosphorus: NDArray[np.floating]
    """Carbon to phosphorus ratio of input to the aboveground metabolic pool [unitless]
    """
    above_structural_phosphorus: NDArray[np.floating]
    """Carbon to phosphorus ratio of input to the aboveground structural pool [unitless]
    """
    woody_phosphorus: NDArray[np.floating]
    """Carbon to phosphorus ratio of input to the woody pool [unitless]"""
    below_metabolic_phosphorus: NDArray[np.floating]
    """Carbon to phosphorus ratio of input to the belowground metabolic pool [unitless]
    """
    below_structural_phosphorus: NDArray[np.floating]
    """Carbon to phosphorus ratio of input to the belowground structural pool [unitless]
    """

    above_structural_lignin: NDArray[np.floating]
    """Lignin proportion of input to the aboveground structural pool.
    
    Units of [kg lignin C (kg C)^-1]
    """
    woody_lignin: NDArray[np.floating]
    """Lignin proportion of input to the woody pool [kg lignin C (kg C)^-1]"""
    below_structural_lignin: NDArray[np.floating]
    """Lignin proportion of input to the belowground structural pool.
     
    Units of [kg lignin C (kg C)^-1]
    """


def calculate_input_chemistries(
    litter_inputs: LitterInputs,
    struct_to_meta_nitrogen_ratio: float,
    struct_to_meta_phosphorus_ratio: float,
) -> InputChemistries:
    """Calculate the chemistries of the input to each litter pool.

    Args:
        litter_inputs: An LitterInputs instance containing the total input of each
            plant biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.
        struct_to_meta_nitrogen_ratio: Ratio of the carbon to nitrogen ratios of
            structural vs metabolic litter pools [unitless]
        struct_to_meta_phosphorus_ratio: Ratio of the carbon to phosphorus ratios of
            structural vs metabolic litter pools [unitless]

    Returns:
        An InputChemistries instance containing the input chemistry for each litter pool
    """

    # Find lignin and nitrogen contents of the litter input flows
    input_lignin = calculate_litter_input_lignin_concentrations(
        litter_inputs=litter_inputs,
    )
    input_c_n_ratios = calculate_litter_input_nitrogen_ratios(
        litter_inputs=litter_inputs,
        struct_to_meta_nitrogen_ratio=struct_to_meta_nitrogen_ratio,
    )
    input_c_p_ratios = calculate_litter_input_phosphorus_ratios(
        litter_inputs=litter_inputs,
        struct_to_meta_phosphorus_ratio=struct_to_meta_phosphorus_ratio,
    )

    return InputChemistries(**input_lignin, **input_c_n_ratios, **input_c_p_ratios)


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
        structural) [kg lignin C (kg C)^-1]
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
        "woody_lignin": lignin_proportion_woody,
        "below_structural_lignin": lignin_proportion_below_structural,
        "above_structural_lignin": lignin_proportion_above_structural,
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
        "woody_nitrogen": c_n_ratio_woody,
        "below_metabolic_nitrogen": c_n_ratio_below_metabolic,
        "below_structural_nitrogen": c_n_ratio_below_structural,
        "above_metabolic_nitrogen": c_n_ratio_above_metabolic,
        "above_structural_nitrogen": c_n_ratio_above_structural,
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
        "woody_phosphorus": c_p_ratio_woody,
        "below_metabolic_phosphorus": c_p_ratio_below_metabolic,
        "below_structural_phosphorus": c_p_ratio_below_structural,
        "above_metabolic_phosphorus": c_p_ratio_above_metabolic,
        "above_structural_phosphorus": c_p_ratio_above_structural,
    }


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
