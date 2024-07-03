"""The ``models.litter.input_partition`` module handles the partitioning of dead plant
and animal matter into the various pools of the litter model.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.logger import LOGGER

# TODO - Add this page and the env_factors page into the API documentation

# TODO - This partition needs to take in information of total mass, lignin content, and
# nitrogen content

# TODO - Generally need to think about lignin units


def split_pool_into_metabolic_and_structural_litter(
    lignin_proportion: NDArray[np.float32],
    carbon_nitrogen_ratio: NDArray[np.float32],
    max_metabolic_fraction: float,
    split_sensitivity: float,
):
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
        ValueError: If any of the metabolic fractions drop below zero.

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
    else:
        return metabolic_fraction


# TODO - It makes sense for the animal pools to be handled here, but need to think about
# how the partition works with the plant partition
# Animals do not contain lignin, so if I used the standard function on animal carcasses
# and excrement the maximum amount (85%) will end up in the metabolic pool, which I
# think is basically fine, when bones aren't explicitly modelled I think this is fine
