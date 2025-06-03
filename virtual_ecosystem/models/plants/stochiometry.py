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


@dataclass
class Tissue(PandasExporter, CohortMethods):
    """A dataclass to hold tissue stochiometry data for a set of plant cohorts.

    This class holds the current quantitiy of a given element (generally N or P) for a
    specific plant tissue type (generally foliage, wood, roots or reproductive tissue).
    The class also holds the ideal ratio of the element for that tissue type. They hold
    an entry for each cohort in the data class.
    """

    element_name: str
    """The name of the element type."""
    tissue_name: str
    """The name of the tissue type."""
    community: Community
    """The community object that the tissue is associated with."""
    # Should this be stored only in stochiometry and not in tissue?

    ideal_ratio: NDArray[np.float64]
    """The ideal ratio of the element for the tissue type."""
    actual_element_mass: NDArray[np.float64]
    """The actual mass of the element for the tissue type."""

    def __post_init__(self) -> None:
        """Initialize the Tissue object."""
        self.actual_element_mass = self.actual_element_mass.squeeze()

    @property
    def carbon_mass(self) -> NDArray[np.float64]:
        """Get the carbon mass for the tissue type.

        This method should be implemented by subclasses to return the carbon mass for
        the specific tissue type.

        Returns:
            The carbon mass for the specified tissue.
        """
        # This method should be implemented by subclasses
        raise NotImplementedError("Carbon mass must be defined in subclasses.")

    @property
    def deficit(self) -> NDArray[np.float64]:
        """Calculate the element deficit for the tissue type.

        Returns:
            The element deficit for the specified tissue.
        """
        return self.ideal_ratio * self.carbon_mass - self.actual_element_mass

    def element_needed_for_growth(
        self, allocation: StemAllocation
    ) -> NDArray[np.float64]:
        """Calculate the element needed for growth for the tissue type.

        Returns:
            The element needed for growth for the specified tissue.
        """
        raise NotImplementedError(
            "Element needed for growth must be defined in subclasses."
        )

    def element_turnover(self, allocation: StemAllocation) -> NDArray[np.float64]:
        """Calculate the element lost to turnover for the tissue type.

        Returns:
            The element lost to turnover for the specified tissue.
        """
        raise NotImplementedError(
            "Element needed for growth must be defined in subclasses."
        )

    @property
    def Cx_ratio(self) -> NDArray[np.float64]:
        """Get the carbon to element ratio for the tissue type.

        Returns:
            The carbon to element ratio for the specified tissue.
        """
        return self.carbon_mass / self.actual_element_mass


class FoliageTissue(Tissue):
    """A class to hold foliage stochiometry data for a set of plant cohorts."""

    # reclaim_ratio: NDArray[np.float64]
    """The ratio of the element that can be r eclaimed from the sensced tissue."""

    def __init__(
        self,
        element_name: str,
        community: Community,
        ideal_ratio: NDArray[np.float64],
        actual_element_mass: NDArray[np.float64],
        reclaim_ratio: NDArray[np.float64],
    ):
        super().__init__(
            element_name=element_name,
            tissue_name="Foliage",
            community=community,
            ideal_ratio=ideal_ratio,
            actual_element_mass=actual_element_mass,
        )
        self.reclaim_ratio = reclaim_ratio
        """The ratio of the element that can be reclaimed from the senesced tissue."""

    @property
    def carbon_mass(self) -> NDArray[np.float64]:
        """Get the carbon mass for foliage tissue.

        Returns:
            The carbon mass for foliage tissue.
        """
        return self.community.stem_allometry.foliage_mass.squeeze()

    def element_needed_for_growth(
        self, allocation: StemAllocation
    ) -> NDArray[np.float64]:
        """Calculate the nitrogen needed for growth for foliage tissue.

        Returns:
            The nitrogen needed for growth for foliage tissue.
        """
        return (allocation.delta_foliage_mass * (1 / self.ideal_ratio)).squeeze()

    def element_turnover(self, allocation: StemAllocation) -> NDArray[np.float64]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The nitrogen lost to turnover for foliage tissue.
        """
        return (
            allocation.foliage_turnover
            * ((1 / self.reclaim_ratio) - (1 / self.Cx_ratio))
        ).squeeze()


class ReproductiveTissue(Tissue):
    """Holds reproductive tissue stochiometry data for a set of plant cohorts."""

    def __init__(
        self,
        element_name: str,
        community: Community,
        ideal_ratio: NDArray[np.float64],
        actual_element_mass: NDArray[np.float64],
    ):
        super().__init__(
            element_name=element_name,
            tissue_name="Reproductive",
            community=community,
            ideal_ratio=ideal_ratio,
            actual_element_mass=actual_element_mass,
        )

    @property
    def carbon_mass(self) -> NDArray[np.float64]:
        """Get the carbon mass for reproductive tissue.

        Returns:
            The carbon mass for reproductive tissue.
        """
        return self.community.stem_allometry.reproductive_tissue_mass.squeeze()

    def element_needed_for_growth(
        self, allocation: StemAllocation
    ) -> NDArray[np.float64]:
        """Calculate the nitrogen needed for growth for reproductive tissue.

        Returns:
            The nitrogen needed for growth for reproductive tissue.
        """
        return (
            allocation.delta_foliage_mass
            * (1 / self.ideal_ratio)
            * self.community.stem_traits.p_foliage_for_reproductive_tissue
        ).squeeze()

    def element_turnover(self, allocation: StemAllocation) -> NDArray[np.float64]:
        """Calculate the element lost to turnover for reproductive tissue.

        Returns:
            The element lost to turnover for reproductive tissue.
        """
        return (allocation.reproductive_tissue_turnover * (1 / self.Cx_ratio)).squeeze()


class WoodTissue(Tissue):
    """A class to hold wood stochiometry data for a set of plant cohorts."""

    def __init__(
        self,
        element_name: str,
        community: Community,
        ideal_ratio: NDArray[np.float64],
        actual_element_mass: NDArray[np.float64],
    ):
        super().__init__(
            element_name=element_name,
            tissue_name="Wood",
            community=community,
            ideal_ratio=ideal_ratio,
            actual_element_mass=actual_element_mass,
        )

    @property
    def carbon_mass(self) -> NDArray[np.float64]:
        """Get the carbon mass for wood tissue.

        Returns:
            The carbon mass for wood tissue.
        """
        return self.community.stem_allometry.stem_mass.squeeze()

    def element_needed_for_growth(
        self, allocation: StemAllocation
    ) -> NDArray[np.float64]:
        """Calculate the nitrogen needed for growth for wood tissue.

        Returns:
            The nitrogen needed for growth for wood tissue.
        """
        return (allocation.delta_stem_mass * (1 / self.ideal_ratio)).squeeze()

    def element_turnover(self, allocation: StemAllocation) -> NDArray[np.float64]:
        """Assume no wood tissue is lost.

        Returns:
            The element lost to turnover for wood tissue.
        """
        return np.zeros(self.community.number_of_cohorts)


class RootTissue(Tissue):
    """A class to hold root stochiometry data for a set of plant cohorts."""

    def __init__(
        self,
        element_name: str,
        community: Community,
        ideal_ratio: NDArray[np.float64],
        actual_element_mass: NDArray[np.float64],
    ):
        super().__init__(
            element_name=element_name,
            tissue_name="Roots",
            community=community,
            ideal_ratio=ideal_ratio,
            actual_element_mass=actual_element_mass,
        )

    @property
    def carbon_mass(self) -> NDArray[np.float64]:
        """Get the carbon mass for root tissue.

        Returns:
            The carbon mass for root tissue.
        """
        return (
            self.community.stem_allometry.foliage_mass * self.community.stem_traits.zeta
        ).squeeze()

    def element_needed_for_growth(
        self, allocation: StemAllocation
    ) -> NDArray[np.float64]:
        """Calculate the nitrogen needed for growth for root tissue.

        Returns:
            The nitrogen needed for growth for root tissue.
        """
        return (
            allocation.delta_foliage_mass
            * (1 / self.ideal_ratio)
            * self.community.stem_traits.zeta
        ).squeeze()

    def element_turnover(self, allocation: StemAllocation) -> NDArray[np.float64]:
        """Calculate the element lost to turnover for root tissue.

        Returns:
            The element lost to turnover for root tissue.
        """
        return (allocation.fine_root_turnover * (1 / self.Cx_ratio)).squeeze()


@dataclass
class StemStochiometry(CohortMethods, PandasExporter):
    """A class holding the ratios of Carbon to Nitrogen and Phosphorous for stems.

    This class holds the current ratios across tissue type for a community object, which
    in essence is a series of cohorts. It acts in parallel with StemAllometry, a class
    attribute of Community.
    """

    tissues: list[Tissue]
    """Tissues for the associated stems."""
    n_cohorts: np.int64
    """The number of cohorts represented by the Stochiometry."""
    community: Community
    """The community object that the stochiometry is associated with."""
    element_surplus: NDArray[np.float64] = field(init=False)
    """The surplus of the element per cohort."""

    def __post_init__(self) -> None:
        """Initialize the element surplus for each cohort."""
        self.element_surplus = np.zeros(self.n_cohorts, dtype=np.float64)

    @property
    def total_element_mass(self) -> NDArray[np.float64]:
        """Calculate the total element mass for each cohort.

        Returns:
            The total nitrogen mass for each cohort.
        """
        mass = np.zeros(self.n_cohorts)
        for tissue in self.tissues:
            mass += tissue.actual_element_mass
        return mass

    @property
    def tissue_deficit(self) -> NDArray[np.float64]:
        """Calculate the element deficit for a tissue type.

        Returns:
            The element deficit for the specified tissue.
        """
        element_deficit = np.zeros(self.n_cohorts)
        for tissue in self.tissues:
            element_deficit += tissue.deficit
        return element_deficit

    def account_for_growth(self, allocation: StemAllocation) -> None:
        """Distribute the element needed for growth to each tissue type.

        This method updates the actual element mass for each tissue type based on the
        element needed for growth calculated from the allocation.

        Args:
            allocation: The allocation object containing the growth allocation data.
        """
        for tissue in self.tissues:
            tissue.actual_element_mass += tissue.element_needed_for_growth(allocation)
            self.element_surplus -= tissue.element_needed_for_growth(allocation)

    def account_for_element_loss_turnover(self, allocation: StemAllocation) -> None:
        """Calculate the total element lost to turnover for each cohort.

        Elements are lost from the tree in the form of turnover, and so an equivalent
        amount of that element is required to replace what was lost. To represent this
        process, the element is allocated from the surplus store in the same quantity
        as turnover. This uses current ratios so that the C:x ratios are maintained.

        Returns:
            The total element lost to turnover for each cohort.
        """
        for tissue in self.tissues:
            self.element_surplus -= tissue.element_turnover(allocation)

    def distribute_deficit(self, cohort: int) -> None:
        """Distribute the nitrogen deficit across the tissue types.

        Args:
            cohort: The cohort to reconcile deficit.
        """
        deficit = self.element_surplus[cohort] * -1

        for tissue in self.tissues:
            tissue.actual_element_mass[cohort] = tissue.actual_element_mass[cohort] - (
                deficit
                * tissue.actual_element_mass[cohort]
                / self.total_element_mass[cohort]
            )

        self.element_surplus[cohort] += deficit

    def distribute_surplus(self, cohort: int) -> None:
        """Distribute the nitrogen surplus across the tissue types for a single cohort.

        Args:
            cohort: The cohort to reconcile surplus.
        """
        if self.element_surplus[cohort] > self.tissue_deficit[cohort]:
            # If there is sufficient surplus N to cover the existing deficit, the
            # amount of the deficit is subtracted from the surplus which persists until
            # the next update. All tissue types are updated to the ideal N ratios.
            self.element_surplus[cohort] = (
                self.element_surplus[cohort] - self.tissue_deficit[cohort]
            )
            for tissue in self.tissues:
                tissue.actual_element_mass[cohort] = (
                    tissue.ideal_ratio[cohort] * tissue.carbon_mass[cohort]
                )
        else:
            # If there is not enough surplus N to cover the deficit, the surplus is
            # distributed across the tissue types in proportion to the N deficit.
            # The surplus is then set to zero.

            for tissue in self.tissues:
                tissue.actual_element_mass[cohort] += (
                    self.element_surplus[cohort]
                    * tissue.deficit[cohort]
                    / self.tissue_deficit[cohort]
                )
            self.element_surplus[cohort] = 0.0
