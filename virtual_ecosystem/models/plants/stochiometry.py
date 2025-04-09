"""The :mod:`~virtual_ecosystem.models.plants.stochiometry` module contains the class
for managing plant cohort stochiometry ratios. The carbon mass is stored in plant
alloemetry or allocation, so this class uses thoses as the anchor weights and stores
CN and CP ratios.

The class holds current CN and CP ratios for foliage, reproductive tissue, wood, and
roots on the cohort level. Each tissue also has an idea CN and CP ratio, which is used
as a comparison in the case of any nutrient deficit. Senesced leaves also have fixed CN
and CP ratios, which is used for leaf turnover.

In the future, the ideal CN and CP ratios will be PFT traits.
"""  # noqa: D205

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from pyrealm.demography.core import CohortMethods, PandasExporter

from virtual_ecosystem.models.plants.constants import PlantsConsts


@dataclass
class StemStochiometry(CohortMethods, PandasExporter):
    """A class holding the ratios of Carbon to Nitrogen and Phosphorous for stems.

    This class holds the current ratios across tissue type for a community object, which
    in essence is a series of cohorts. It acts in parallel with SteAllometry, a class
    attribute of Community.
    """

    # Init vars
    plant_constants: PlantsConsts
    """The plant constants used in the model."""
    n_cohorts: int
    """The number of cohorts in the community."""

    # Post-init vars
    cn_reproductive_tissue: NDArray[np.float64] = field(init=False)
    """An array of carbon to nitrogen ratios for reproductive tissue."""
    cp_reproductive_tissue: NDArray[np.float64] = field(init=False)
    """An array of carbon to phosphorous ratios for reproductive tissue."""

    cn_foliage: NDArray[np.float64] = field(init=False)
    """An array of carbon to nitrogen ratios for foliage."""
    cp_foliage: NDArray[np.float64] = field(init=False)
    """An array of carbon to phosphorous ratios for foliage."""

    cn_wood: NDArray[np.float64] = field(init=False)
    """An array of carbon to nitrogen ratios for wood."""
    cp_wood: NDArray[np.float64] = field(init=False)
    """An array of carbon to phosphorous ratios for wood."""

    cn_roots: NDArray[np.float64] = field(init=False)
    """An array of carbon to nitrogen ratios for roots."""
    cp_roots: NDArray[np.float64] = field(init=False)
    """An array of carbon to phosphorous ratios for roots."""

    def __post_init__(
        self,
    ) -> None:
        """Initialise the stochiometry class.

        Args:
            plant_constants: The plant constants used in the model.
            len_cohort: The number of cohorts in the community.
        """

        # Initialise the arrays
        self.cn_reproductive_tissue = np.full(
            self.n_cohorts,
            self.plant_constants.plant_reproductive_tissue_turnover_c_n_ratio,
        )
        self.cp_reproductive_tissue = np.full(
            self.n_cohorts,
            self.plant_constants.plant_reproductive_tissue_turnover_c_p_ratio,
        )

        self.cn_foliage = np.full(
            self.n_cohorts, self.plant_constants.foliage_c_n_ratio
        )
        self.cp_foliage = np.full(
            self.n_cohorts, self.plant_constants.foliage_c_p_ratio
        )

        self.cn_wood = np.full(self.n_cohorts, self.plant_constants.deadwood_c_n_ratio)
        self.cp_wood = np.full(self.n_cohorts, self.plant_constants.deadwood_c_p_ratio)

        self.cn_roots = np.full(
            self.n_cohorts, self.plant_constants.root_turnover_c_n_ratio
        )
        self.cp_roots = np.full(
            self.n_cohorts, self.plant_constants.root_turnover_c_p_ratio
        )
