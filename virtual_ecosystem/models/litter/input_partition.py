"""The ``models.litter.input_partition`` module handles the partitioning of plant
matter into the various pools of the litter model. This plant matter comes from both
natural tissue death as well as from mechanical inefficiencies in herbivory.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.litter.constants import LitterConsts


@dataclass
class InputDetails:
    """The full details of the input to the litter model."""

    leaf_mass: NDArray[np.float32]
    """Total leaf input mass to litter [kg C m^-2]"""
    root_mass: NDArray[np.float32]
    """Total root input mass to litter [kg C m^-2]"""
    deadwood_mass: NDArray[np.float32]
    """Total deadwood input mass to litter [kg C m^-2]"""
    reprod_mass: NDArray[np.float32]
    """Total plant reproductive tissue input mass to litter [kg C m^-2]"""

    leaf_lignin: NDArray[np.float32]
    """Lignin proportion of leaf input [unitless]"""
    root_lignin: NDArray[np.float32]
    """Lignin proportion of root input [unitless]"""
    deadwood_lignin: NDArray[np.float32]
    """Lignin proportion of deadwood input [unitless]"""
    reprod_lignin: NDArray[np.float32]
    """Lignin proportion of reproductive tissue input [unitless]"""

    leaf_nitrogen: NDArray[np.float32]
    """Carbon nitrogen ratio of leaf input [unitless]"""
    root_nitrogen: NDArray[np.float32]
    """Carbon nitrogen ratio of root input [unitless]"""
    deadwood_nitrogen: NDArray[np.float32]
    """Carbon nitrogen ratio of deadwood input [unitless]"""
    reprod_nitrogen: NDArray[np.float32]
    """Carbon nitrogen ratio of reproductive tissue input [unitless]"""

    leaf_phosphorus: NDArray[np.float32]
    """Carbon phosphorus ratio of leaf input [unitless]"""
    root_phosphorus: NDArray[np.float32]
    """Carbon phosphorus ratio of root input [unitless]"""
    deadwood_phosphorus: NDArray[np.float32]
    """Carbon phosphorus ratio of deadwood input [unitless]"""
    reprod_phosphorus: NDArray[np.float32]
    """Carbon phosphorus ratio of reproductive tissue input [unitless]"""

    leaves_meta_split: NDArray[np.float32]
    """Fraction of leaf input that goes to metabolic litter [unitless]"""
    reproduct_meta_split: NDArray[np.float32]
    """Fraction of leaf input that goes to metabolic litter [unitless]"""
    roots_meta_split: NDArray[np.float32]
    """Fraction of leaf input that goes to metabolic litter [unitless]"""

    input_woody: NDArray[np.float32]
    """Total input to the woody litter pool [kg C m^-2]"""
    input_above_metabolic: NDArray[np.float32]
    """Total input to the above ground metabolic litter pool [kg C m^-2]"""
    input_above_structural: NDArray[np.float32]
    """Total input to the above ground structural litter pool [kg C m^-2]"""
    input_below_metabolic: NDArray[np.float32]
    """Total input to the below ground metabolic litter pool [kg C m^-2]"""
    input_below_structural: NDArray[np.float32]
    """Total input to the below ground structural litter pool [kg C m^-2]"""


class InputPartition:
    """This class handles the partitioning of plant matter between litter pools.

    This class contains methods to calculate the partition of input plant matter between
    the different litter pools based on the contents of the `data` object.
    """

    def __init__(self, data: Data):
        self.data = data

    def determine_all_plant_to_litter_flows(
        self, constants: LitterConsts
    ) -> InputDetails:
        """Determine the total flow to each litter pool from dead plant matter.

        This method first combines the two different input streams for dead plant matter
        (plant tissue death and herbivory waste) to find the total input of each plant
        biomass type. This total is then used in the subsequent calculations.

        Args:
            constants: Set of constants for the litter model.

        Returns:
            An InputDetails instance containing the total input of each plant biomass
            type, the proportion of the input that goes to the relevant metabolic pool
            for each input type (expect deadwood) and the total input into each litter
            pool.
        """

        # Find the total input for each plant matter type
        total_input = self.combine_input_sources()

        # Find the plant inputs to each of the litter pools
        metabolic_splits = calculate_metabolic_proportions_of_input(
            total_input=total_input, constants=constants
        )

        plant_inputs = partion_plant_inputs_between_pools(
            total_input=total_input, metabolic_splits=metabolic_splits
        )

        return InputDetails(**metabolic_splits, **plant_inputs, **total_input)

    def combine_input_sources(self) -> dict[str, NDArray[np.float32]]:
        """Combine the plant death and herbivory inputs into a single total input.

        The total input for each plant matter type (leaves, roots, deadwood,
        reproductive tissue) is returned, the chemical concentration of each of these
        new pools is also calculated.

        TODO - At the moment there is only leaf input defined so this function doesn't
        really do anything for the other types of plant matter. Once input is defined
        for them this function should be updated to actually do something with them.

        Returns:
            A dictionary containing the total pool size for each input pools [kg C
            m^-3], as well as the chemistry proportions (lignin, nitrogen and
            phosphorus) of each of these pools [unitless].
        """

        # Calculate totals for each plant matter type
        leaf_total = (
            self.data["leaf_turnover"] + self.data["herbivory_waste_leaf_carbon"]
        )
        root_total = self.data["root_turnover"]
        deadwood_total = self.data["deadwood_production"]
        reprod_total = self.data["plant_reproductive_tissue_turnover"]

        # Calculate leaf lignin concentrations for each combined pool
        leaf_lignin = (
            self.data["leaf_turnover_lignin"] * self.data["leaf_turnover"]
            + self.data["herbivory_waste_leaf_lignin"]
            * self.data["herbivory_waste_leaf_carbon"]
        ) / (leaf_total)
        root_lignin = self.data["root_turnover_lignin"]
        deadwood_lignin = self.data["deadwood_lignin"]
        reprod_lignin = self.data["plant_reproductive_tissue_turnover_lignin"]

        # Calculate leaf nitrogen concentrations for each combined pool
        leaf_nitrogen = (
            self.data["leaf_turnover_c_n_ratio"] * self.data["leaf_turnover"]
            + self.data["herbivory_waste_leaf_nitrogen"]
            * self.data["herbivory_waste_leaf_carbon"]
        ) / (leaf_total)
        root_nitrogen = self.data["root_turnover_c_n_ratio"]
        deadwood_nitrogen = self.data["deadwood_c_n_ratio"]
        reprod_nitrogen = self.data["plant_reproductive_tissue_turnover_c_n_ratio"]

        # Calculate leaf phosphorus concentrations for each combined pool
        leaf_phosphorus = (
            self.data["leaf_turnover_c_p_ratio"] * self.data["leaf_turnover"]
            + self.data["herbivory_waste_leaf_phosphorus"]
            * self.data["herbivory_waste_leaf_carbon"]
        ) / (leaf_total)
        root_phosphorus = self.data["root_turnover_c_p_ratio"]
        deadwood_phosphorus = self.data["deadwood_c_p_ratio"]
        reprod_phosphorus = self.data["plant_reproductive_tissue_turnover_c_p_ratio"]

        return {
            "leaf_mass": leaf_total.to_numpy(),
            "root_mass": root_total.to_numpy(),
            "deadwood_mass": deadwood_total.to_numpy(),
            "reprod_mass": reprod_total.to_numpy(),
            "leaf_lignin": leaf_lignin.to_numpy(),
            "root_lignin": root_lignin.to_numpy(),
            "deadwood_lignin": deadwood_lignin.to_numpy(),
            "reprod_lignin": reprod_lignin.to_numpy(),
            "leaf_nitrogen": leaf_nitrogen.to_numpy(),
            "root_nitrogen": root_nitrogen.to_numpy(),
            "deadwood_nitrogen": deadwood_nitrogen.to_numpy(),
            "reprod_nitrogen": reprod_nitrogen.to_numpy(),
            "leaf_phosphorus": leaf_phosphorus.to_numpy(),
            "root_phosphorus": root_phosphorus.to_numpy(),
            "deadwood_phosphorus": deadwood_phosphorus.to_numpy(),
            "reprod_phosphorus": reprod_phosphorus.to_numpy(),
        }


def calculate_metabolic_proportions_of_input(
    total_input: dict[str, NDArray[np.float32]], constants: LitterConsts
) -> dict[str, NDArray[np.float32]]:
    """Calculate the proportion of each input type that flows to the metabolic pool.

    This function is used for roots, leaves and reproductive tissue, but not deadwood
    because everything goes into a single woody litter pool. It is not used for animal
    inputs either as they all flow into just the metabolic pool.

    Args:
        total_input: The total pool size for each input pool [kg C m^-3], as well as
            the chemical proportions (lignin, nitrogen and phosphorus) of each of these
            pools [unitless].
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
    total_input: dict[str, NDArray[np.float32]],
    metabolic_splits: dict[str, NDArray[np.float32]],
):
    """Function to partition input biomass between the various litter pools.

    All deadwood is added to the woody litter pool. Reproductive biomass (fruits and
    flowers) and leaves are split between the above ground metabolic and structural
    pools based on lignin concentration and carbon nitrogen ratios. Root biomass is
    split between the below ground metabolic and structural pools based on lignin
    concentration and carbon nitrogen ratios.

    Args:
        total_input: The total pool size for each input pool [kg C m^-2], as well as
            the chemical proportions (lignin, nitrogen and phosphorus) of each of
            these pools [unitless].
        metabolic_splits: Dictionary containing the proportion of each input that
            goes to the relevant metabolic pool. This is for three input types:
            leaves, reproductive tissues and roots [unitless]

    Returns:
        A dictionary containing the biomass flow into each of the five litter pools
        (woody, above ground metabolic, above ground structural, below ground
        metabolic and below ground structural)
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
        "input_woody": woody_input,
        "input_above_metabolic": above_ground_metabolic_input,
        "input_above_structural": above_ground_strutural_input,
        "input_below_metabolic": below_ground_metabolic_input,
        "input_below_structural": below_ground_structural_input,
    }


def split_pool_into_metabolic_and_structural_litter(
    lignin_proportion: NDArray[np.float32],
    carbon_nitrogen_ratio: NDArray[np.float32],
    carbon_phosphorus_ratio: NDArray[np.float32],
    max_metabolic_fraction: float,
    split_sensitivity_nitrogen: float,
    split_sensitivity_phosphorus: float,
) -> NDArray[np.float32]:
    """Calculate the split of input biomass between metabolic and structural pools.

    This division depends on the lignin and nitrogen content of the input biomass, the
    functional form is taken from :cite:t:`parton_dynamics_1988`.

    Args:
        lignin_proportion: Proportion of input biomass carbon that is lignin [kg lignin
            kg C^-1]
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
