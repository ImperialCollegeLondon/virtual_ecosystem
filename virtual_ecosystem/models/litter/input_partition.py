"""The ``models.litter.input_partition`` module handles the partitioning of plant
matter into the various pools of the litter model. This plant matter comes from both
natural tissue death as well as from mechanical inefficiencies in herbivory.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray

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
