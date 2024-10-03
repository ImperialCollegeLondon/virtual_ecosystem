"""The ``models.litter.input_partition`` module handles the partitioning of plant
matter into the various pools of the litter model. This plant matter comes from both
natural tissue death as well as from mechanical inefficiencies in herbivory.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.litter.constants import LitterConsts


class InputPartition:
    """This class handles the partitioning of plant matter between litter pools.

    This class contains methods to calculate the partition of input plant matter between
    the different litter pools based on the contents of the `data` object.
    """

    def __init__(self, data: Data):
        self.data = data

    def determine_all_plant_to_litter_flows(
        self, constants: LitterConsts
    ) -> tuple[dict[str, NDArray[np.float32]], dict[str, NDArray[np.float32]]]:
        """Determine the total flow to each litter pool from dead plant matter.

        TODO - At the moment this doesn't combine the different input flows, but it will
        soon. And when it does I need to describe it in this docstring.

        Args:
            constants: Set of constants for the litter model.

        Returns:
            Two dictionaries, the first of which provides the proportion of the input
            that goes to the relevant metabolic pool for each input type (expect
            deadwood) [unitless]. The second dictionary provides the total plant biomass
            flow into each of the litter pools [kg C m^-2].
        """

        # Find the plant inputs to each of the litter pools
        metabolic_splits = self.calculate_metabolic_proportions_of_input(
            constants=constants
        )

        plant_inputs = self.partion_plant_inputs_between_pools(
            metabolic_splits=metabolic_splits
        )

        return metabolic_splits, plant_inputs

    def combine_input_sources(self) -> dict[str, DataArray]:
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
            "leaf_mass": leaf_total,
            "root_mass": root_total,
            "deadwood_mass": deadwood_total,
            "reprod_mass": reprod_total,
            "leaf_lignin": leaf_lignin,
            "root_lignin": root_lignin,
            "deadwood_lignin": deadwood_lignin,
            "reprod_lignin": reprod_lignin,
            "leaf_nitrogen": leaf_nitrogen,
            "root_nitrogen": root_nitrogen,
            "deadwood_nitrogen": deadwood_nitrogen,
            "reprod_nitrogen": reprod_nitrogen,
            "leaf_phosphorus": leaf_phosphorus,
            "root_phosphorus": root_phosphorus,
            "deadwood_phosphorus": deadwood_phosphorus,
            "reprod_phosphorus": reprod_phosphorus,
        }

    def calculate_metabolic_proportions_of_input(
        self, constants: LitterConsts
    ) -> dict[str, NDArray[np.float32]]:
        """Calculate the proportion of each input type that flows to the metabolic pool.

        This function is used for roots, leaves and reproductive tissue, but not
        deadwood because everything goes into a single woody litter pool. It is not used
        for animal inputs either as they all flow into just the metabolic pool.

        Args:
            constants: Set of constants for the litter model.

        Returns:
            A dictionary containing the proportion of the input that goes to the
            relevant metabolic pool. This is for three input types: leaves, reproductive
            tissues and roots [unitless]
        """

        # Calculate split of each input biomass type
        leaves_metabolic_split = split_pool_into_metabolic_and_structural_litter(
            lignin_proportion=self.data["leaf_turnover_lignin"].to_numpy(),
            carbon_nitrogen_ratio=self.data["leaf_turnover_c_n_ratio"].to_numpy(),
            carbon_phosphorus_ratio=self.data["leaf_turnover_c_p_ratio"].to_numpy(),
            max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
        )

        repoduct_metabolic_split = split_pool_into_metabolic_and_structural_litter(
            lignin_proportion=self.data[
                "plant_reproductive_tissue_turnover_lignin"
            ].to_numpy(),
            carbon_nitrogen_ratio=self.data[
                "plant_reproductive_tissue_turnover_c_n_ratio"
            ].to_numpy(),
            carbon_phosphorus_ratio=self.data[
                "plant_reproductive_tissue_turnover_c_p_ratio"
            ].to_numpy(),
            max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
        )

        roots_metabolic_split = split_pool_into_metabolic_and_structural_litter(
            lignin_proportion=self.data["root_turnover_lignin"].to_numpy(),
            carbon_nitrogen_ratio=self.data["root_turnover_c_n_ratio"].to_numpy(),
            carbon_phosphorus_ratio=self.data["root_turnover_c_p_ratio"].to_numpy(),
            max_metabolic_fraction=constants.max_metabolic_fraction_of_input,
            split_sensitivity_nitrogen=constants.metabolic_split_nitrogen_sensitivity,
            split_sensitivity_phosphorus=constants.metabolic_split_phosphorus_sensitivity,
        )

        return {
            "leaves": leaves_metabolic_split,
            "reproductive": repoduct_metabolic_split,
            "roots": roots_metabolic_split,
        }

    def partion_plant_inputs_between_pools(
        self, metabolic_splits: dict[str, NDArray[np.float32]]
    ):
        """Function to partition input biomass between the various litter pools.

        All deadwood is added to the woody litter pool. Reproductive biomass (fruits and
        flowers) and leaves are split between the above ground metabolic and structural
        pools based on lignin concentration and carbon nitrogen ratios. Root biomass is
        split between the below ground metabolic and structural pools based on lignin
        concentration and carbon nitrogen ratios.

        Args:
            metabolic_splits: Dictionary containing the proportion of each input that
                goes to the relevant metabolic pool. This is for three input types:
                leaves, reproductive tissues and roots [unitless]

        Returns:
            A dictionary containing the biomass flow into each of the five litter pools
            (woody, above ground metabolic, above ground structural, below ground
            metabolic and below ground structural)
        """

        # Calculate input to each of the five litter pools
        woody_input = self.data["deadwood_production"]
        above_ground_metabolic_input = (
            metabolic_splits["leaves"] * self.data["leaf_turnover"]
            + metabolic_splits["reproductive"]
            * self.data["plant_reproductive_tissue_turnover"]
        )
        above_ground_strutural_input = (1 - metabolic_splits["leaves"]) * self.data[
            "leaf_turnover"
        ] + (1 - metabolic_splits["reproductive"]) * self.data[
            "plant_reproductive_tissue_turnover"
        ]
        below_ground_metabolic_input = (
            metabolic_splits["roots"] * self.data["root_turnover"]
        )
        below_ground_structural_input = (1 - metabolic_splits["roots"]) * self.data[
            "root_turnover"
        ]

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
