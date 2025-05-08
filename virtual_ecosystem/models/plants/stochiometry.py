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
from pyrealm.demography.community import Community
from pyrealm.demography.core import CohortMethods, PandasExporter
from pyrealm.demography.tmodel import StemAllocation

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
    community: Community
    """The Community object for the stochiometry."""

    # Post-init vars
    n_reproductive_tissue: NDArray[np.float64] = field(init=False)
    """Per stem Nitrogen mass of reproductive tissue for each cohort."""
    p_reproductive_tissue: NDArray[np.float64] = field(init=False)
    """Per stem Phosphorous mass of reproductive tissue for each cohort."""

    n_foliage: NDArray[np.float64] = field(init=False)
    """Per stem Nitrogen mass of foliage for each cohort."""
    p_foliage: NDArray[np.float64] = field(init=False)
    """Per stem Phosphorous mass of foliage for each cohort."""

    n_wood: NDArray[np.float64] = field(init=False)
    """Per stem Nitrogen mass of wood for each cohort."""
    p_wood: NDArray[np.float64] = field(init=False)
    """Per stem Phosphorous mass of wood for each cohort."""

    n_roots: NDArray[np.float64] = field(init=False)
    """Per stem Nitrogen mass of roots for each cohort."""
    p_roots: NDArray[np.float64] = field(init=False)
    """Per stem Phosphorous mass of roots for each cohort."""

    n_surplus: NDArray[np.float64] = field(init=False)
    """Per stem Nitrogen surplus (or deficit) for each cohort."""
    p_surplus: NDArray[np.float64] = field(init=False)
    """Per stem Phosphorous surplus (or deficit) for each cohort."""

    def __post_init__(
        self,
    ) -> None:
        """Initialise the stochiometry class.

        TODO: Where do these nutrients come from?

        Args:
            community: The Community object that parallels the Stochiometry.
        """

        # Initialise the arrays
        self.n_reproductive_tissue = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.plant_reproductive_tissue_turnover_c_n_ratio
            * self.community.stem_allometry.reproductive_tissue_mass,
        )
        self.p_reproductive_tissue = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.plant_reproductive_tissue_turnover_c_p_ratio
            * self.community.stem_allometry.reproductive_tissue_mass,
        )

        self.n_foliage = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.foliage_c_n_ratio
            * self.community.stem_allometry.foliage_mass,
        )
        self.p_foliage = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.foliage_c_p_ratio
            * self.community.stem_allometry.foliage_mass,
        )

        self.n_wood = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.deadwood_c_n_ratio
            * self.community.stem_allometry.stem_mass,
        )
        self.p_wood = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.deadwood_c_p_ratio
            * self.community.stem_allometry.stem_mass,
        )

        self.n_roots = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.root_turnover_c_n_ratio
            * self.community.stem_traits.zeta
            * self.community.stem_allometry.foliage_mass,
        )
        self.p_roots = np.full(
            self.community.number_of_cohorts,
            self.plant_constants.root_turnover_c_p_ratio
            * self.community.stem_traits.zeta
            * self.community.stem_allometry.foliage_mass,
        )

        self.n_surplus = np.full(self.community.number_of_cohorts, 0.0)
        self.p_surplus = np.full(self.community.number_of_cohorts, 0.0)

    @property
    def total_n(self) -> NDArray[np.float64]:
        """Calculate the total nitrogen mass for each cohort.

        Returns:
            The total nitrogen mass for each cohort.
        """
        return (
            self.n_foliage + self.n_wood + self.n_roots + self.n_reproductive_tissue
        ).squeeze()

    def total_p(self) -> NDArray[np.float64]:
        """Calculate the total phosphorous mass for each cohort.

        Returns:
            The total phosphorous mass for each cohort.
        """
        return self.p_foliage + self.p_wood + self.p_roots + self.p_reproductive_tissue

    @property
    def n_foliage_deficit(self) -> NDArray[np.float64]:
        """Calculate the nitrogen deficit for foliage.

        Returns:
            The nitrogen deficit for foliage.
        """
        return (
            self.plant_constants.foliage_c_n_ratio
            * self.community.stem_allometry.foliage_mass
            - self.n_foliage
        ).squeeze()

    @property
    def n_wood_deficit(self) -> NDArray[np.float64]:
        """Calculate the nitrogen deficit for wood.

        Returns:
            The nitrogen deficit for wood.
        """
        return (
            self.plant_constants.deadwood_c_n_ratio
            * self.community.stem_allometry.stem_mass
            - self.n_wood
        ).squeeze()

    @property
    def n_roots_deficit(self) -> NDArray[np.float64]:
        """Calculate the nitrogen deficit for roots.

        Returns:
            The nitrogen deficit for roots.
        """
        return (
            self.plant_constants.root_turnover_c_n_ratio
            * self.community.stem_traits.zeta
            * self.community.stem_allometry.foliage_mass
            - self.n_roots
        ).squeeze()

    @property
    def n_reproductive_tissue_deficit(self) -> NDArray[np.float64]:
        """Calculate the nitrogen deficit for reproductive tissue.

        Returns:
            The nitrogen deficit for reproductive tissue.
        """
        return (
            self.plant_constants.plant_reproductive_tissue_turnover_c_n_ratio
            * self.community.stem_allometry.reproductive_tissue_mass
            - self.n_reproductive_tissue
        ).squeeze()

    @property
    def n_tissue_deficit(self) -> NDArray[np.float64]:
        """Calculate the nitrogen deficit for each cohort.

        Returns:
            The nitrogen deficit for each cohort.
        """

        return (
            self.n_foliage_deficit
            + self.n_wood_deficit
            + self.n_roots_deficit
            + self.n_reproductive_tissue_deficit
        )

    def n_for_growth(self, allocation: StemAllocation) -> NDArray[np.float64]:
        """Calculate the nitrogen required for growth for each cohort.

        Returns:
            The nitrogen available for growth for each cohort.
        """

        n_needed_for_foliage_growth = allocation.delta_foliage_mass * (
            1 / self.plant_consts["foliage_c_n_ratio"]
        )

        n_needed_for_stem_growth = allocation.delta_stem_mass * (
            1 / self.plant_consts["deadwood_c_n_ratio"]
        )

        n_needed_for_rt_growth = (
            allocation.delta_foliage_mass
            * (1 / self.plant_consts["plant_reproductive_tissue_turnover_c_n_ratio"])
            * self.community.stem_allometry.p_foliage_for_reproductive_tissue
        )

        n_needed_for_growth = (
            n_needed_for_foliage_growth
            + n_needed_for_stem_growth
            + n_needed_for_rt_growth
        )

        return n_needed_for_growth

    @property
    def cn_ratio_foliage(self) -> NDArray[np.float64]:
        """Get the carbon to nitrogen ratio for foliage."""
        return self.community.stem_allometry.foliage_mass / self.n_foliage

    @property
    def cn_ratio_roots(self) -> NDArray[np.float64]:
        """Get the carbon to nitrogen ratio for roots."""
        return (
            self.community.stem_traits.zeta * self.community.stem_allometry.foliage_mass
        ) / self.n_roots

    @property
    def cn_ratio_reproductive_tissue(self) -> NDArray[np.float64]:
        """Get the carbon to nitrogen ratio for reproductive tissue."""
        return (
            self.community.stem_allometry.reproductive_tissue_mass
            / self.n_reproductive_tissue
        )

    def n_for_foliage_growth(self, delta_foliage_mass) -> NDArray[np.float64]:
        """Get the nitrogen needed for foliage growth."""
        return (
            (1 / self.plant_constants.foliage_c_n_ratio) * delta_foliage_mass
        ).squeeze()

    def distribute_deficit(self, cohort: int) -> None:
        """Distribute the nitrogen deficit across the tissue types.

        Args:
            cohort: The cohort to reconcile deficit.
        """
        deficit = self.n_surplus[cohort] * -1

        self.n_foliage[cohort] = self.n_foliage[cohort] - (
            deficit * self.n_foliage[cohort] / self.total_n[cohort]
        )

        self.n_wood[cohort] = self.n_wood[cohort] - (
            deficit * self.n_wood[cohort] / self.total_n[cohort]
        )
        self.n_roots[cohort] -= deficit * self.n_roots[cohort] / self.total_n[cohort]
        self.n_reproductive_tissue[cohort] -= (
            deficit * self.n_reproductive_tissue[cohort] / self.total_n[cohort]
        )
        self.n_surplus[cohort] += deficit

    def distribute_surplus(self, cohort: int) -> None:
        """Distribute the nitrogen surplus across the tissue types for a single cohort.

        Args:
            cohort: The cohort to reconcile surplus.
        """
        if self.n_surplus[cohort] > self.n_tissue_deficit[cohort]:
            # If there is sufficient surplus N to cover the existing deficit, the
            # amount of the deficit is subtracted from the surplus which persists until
            # the next update. All tissue types are updated to the ideal N ratios.
            self.n_surplus[cohort] = (
                self.n_surplus[cohort] - self.n_tissue_deficit[cohort]
            )
            self.n_foliage[cohort] = (
                self.plant_constants.plant_reproductive_tissue_turnover_c_n_ratio
                * self.community.stem_allometry.foliage_mass.squeeze()[cohort]
            )
            self.n_wood[cohort] = (
                # self.plant_constants.deadwood_c_n_ratio *
                self.community.stem_allometry.stem_mass.squeeze()[cohort]
            )
            self.n_roots[cohort] = (
                self.plant_constants.root_turnover_c_n_ratio
                * self.community.stem_traits.zeta[cohort]
                * self.community.stem_allometry.foliage_mass.squeeze()[cohort]
            )
            self.n_reproductive_tissue[cohort] = (
                self.plant_constants.plant_reproductive_tissue_turnover_c_n_ratio
                * self.community.stem_allometry.reproductive_tissue_mass.squeeze()[
                    cohort
                ]
            )
        else:
            # If there is not enough surplus N to cover the deficit, the surplus is
            # distributed across the tissue types in proportion to the N deficit.
            # The surplus is then set to zero.

            self.n_foliage[cohort] += (
                self.n_surplus[cohort]
                * self.n_foliage_deficit[cohort]
                / self.n_tissue_deficit[cohort]
            )
            self.n_wood[cohort] += (
                self.n_surplus[cohort]
                * self.n_wood_deficit[cohort]
                / self.n_tissue_deficit[cohort]
            )
            self.n_roots[cohort] += (
                self.n_surplus[cohort]
                * self.n_roots_deficit[cohort]
                / self.n_tissue_deficit[cohort]
            )
            self.n_reproductive_tissue[cohort] += (
                self.n_surplus[cohort]
                * self.n_reproductive_tissue_deficit[cohort]
                / self.n_tissue_deficit[cohort]
            )
            self.n_surplus[cohort] = 0.0
