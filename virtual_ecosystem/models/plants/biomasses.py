"""The :mod:`~virtual_ecosystem.models.plants.biomasses` module contains the class
for managing plant cohort carbon biomass along with the biomasses of all elements being
tracked stochiometrically within a simulation. The class contains representations of the
carbon mass and element masses within individual tissues and provides methods to balance
stoichiometric nutrients across tissues.

The theoretical tissue masses for individuals in a cohort are derived from the T Model
predictions for the stem and the elemental masses are currently populated using the
ideal ratio of those elements for each tissue. Growth is modelled using allocation of
NPP from the T Model. However, the actual realised masses of different tissues can
differ from the theory due to herbivory and fruit production, so this class is used to
track the actual carbon masses realised by individuals through the simulation.

The module define a base class for tissues and then currently four tissue types.

FoliageTissue:
    # Has different ratios in turnover mass

    biomass: foliage_mass
    turnover_biomass: foliage_turnover
    growth_biomass: delta_foliage_mass

    ideal_ratio: foliage_c_{elem.lower()}_ratio
    turnover_ratio: leaf_turnover_c_{elem.lower()}_ratio

    TODO - check to make sure turnover foliage doesn't get relatively _enriched_ if the
           plant is severely nutrient depleted.

ReproductiveTissue:
    # Same ratios; has turnover

    biomass: reproductive_tissue_mass
    turnover_biomass: reproductive_tissue_turnover
    growth_biomass: foliage_tissue * p_foliage_for_reproductive_tissue

    ideal_ratio: not defined - identical to turnover ratio
    turnover_ratio: plant_reproductive_tissue_turnover_c_{elem.lower()}_ratio

RootTissue:
    # Same ratios; has turnover

    biomass: fine_root_mass
    turnover_biomass: fine_root_turnover
    growth_biomass: delta_foliage_mass * zeta * sla

    ideal_ratio: not defined - identical to turnover ratio
    turnover_ratio: root_turnover_c_{elem.lower()}_ratio

WoodTissue
    # No turnover at present, so same ratios doesn't really make sense, but if there was
      turnover it probably would be at these ratios.

    biomass: stem_mass
    turnover_biomass: not defined, no stem turnover
    growth_biomass: delta_stem_mass

    ideal_ratio: deadwood_c_{elem.lower()}_ratio
    turnover_ratio: not defined (because there is no turnover)


"""  # noqa: D205

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from pyrealm.demography.community import Community
from pyrealm.demography.core import CohortMethods, PandasExporter
from pyrealm.demography.tmodel import StemAllocation

from virtual_ecosystem.models.plants.functional_types import ExtraTraitsPFT


@dataclass
class Element:
    """Stochiometric elemental masses for cohorts in a community."""

    name: str
    """The element name."""
    ideal_ratio: NDArray[np.floating]
    """The ideal ratio of the element for the tissue type."""
    actual_element_mass: NDArray[np.floating]
    """The actual mass of the element for the tissue type."""
    turnover_ratio: NDArray[np.floating]
    """What to do with this on non-reclaiming tissues."""

    def append(self, other: Element) -> None:
        """Appends new data representing new cohorts onto an element instance."""
        self.ideal_ratio = np.append(self.ideal_ratio, other.ideal_ratio)
        self.actual_element_mass = np.append(
            self.actual_element_mass, other.actual_element_mass
        )
        self.turnover_ratio = np.append(self.turnover_ratio, other.turnover_ratio)


@dataclass
class TissueABC(ABC):
    """A dataclass to hold tissue stoichiometry data for a set of plant cohorts.

    This class holds the current quantity of a given element (generally N or P) for a
    specific plant tissue type (generally foliage, wood, roots or reproductive tissue).
    The class also holds the ideal ratio of the element for that tissue type. They hold
    an entry for each cohort in the data class.
    """

    tissue_name: ClassVar[str]
    """A tissue name for derived classes."""

    community: Community
    """The community object that the tissue is associated with."""
    # TODO: consider where best to store shared attributes like community.

    carbon_mass: NDArray[np.floating]

    element_masses: dict[str, Element]

    @classmethod
    @abstractmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of Tissue based on the PFT traits."""

    @property
    def deficit(self) -> dict[str, NDArray[np.floating]]:
        """Calculate the element deficit (ideal mass - actual mass) for the tissue.

        Returns:
            The element deficit for the specified tissue.
        """
        return {
            ky: (self.carbon_mass / elem.ideal_ratio) - elem.actual_element_mass
            for ky, elem in self.element_masses.items()
        }

    @property
    def get_elemental_masses(self) -> dict[str, NDArray[np.floating]]:
        """Get the current element masses for the tissue.

        Returns:
            The element deficit for the specified tissue.
        """
        return {
            ky: elem.actual_element_mass for ky, elem in self.element_masses.items()
        }

    def add_elemental_masses(self, masses: dict[str, NDArray[np.floating]]) -> None:
        """Return the current element masses for the tissue.

        Returns:
            The element deficit for the specified tissue.
        """

        try:
            for ky, elem in self.element_masses.items():
                elem.actual_element_mass += masses[ky]
        except KeyError:
            raise ValueError("add_elemental_masses missing required element.")
        except ValueError:
            raise ValueError("Error adding elements mass - incompatible shapes.")

    @property
    def Cx_ratio(self) -> dict[str, NDArray[np.floating]]:
        """Get the carbon to element ratio for the tissue type.

        Returns:
            The carbon to element ratio for the specified tissue.
        """
        return {
            ky: self.carbon_mass / elem.actual_element_mass
            for ky, elem in self.element_masses.items()
        }

    def as_array(
        self, deficit: bool = False, with_carbon: bool = False
    ) -> NDArray[np.floating]:
        """Utility method to return tissue masses as an array.

        TODO: The internals of this class may switch over to array based, this is a
              placeholder API for that change.

        Args:
            deficit: Return the deficit masses not the actual masses.
            with_carbon: Should carbon mass be included in the array.
        """

        if deficit:
            elemental_masses = list(self.deficit.values())
        else:
            elemental_masses = [
                elem.actual_element_mass for elem in self.element_masses.values()
            ]
        if with_carbon:
            return np.stack(
                [self.carbon_mass, *elemental_masses],
            )

        return np.stack(elemental_masses)

    @abstractmethod
    def elements_needed_for_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the elements needed for growth for the tissue type."""

    @abstractmethod
    def tissue_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element lost to turnover for the tissue type.

        TODO - possibly retire this in favour of extract turnover? Do we ever need to
               know what the element loss would be _without_ removing the masses?
        """

    @abstractmethod
    def extract_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Extract the tissue elemental masses associated with turnover.

        This method should return a dictionary of elemental masses from turnover and
        reduce the tissue instance by those masses.

        TODO: this returns Carbon too - do we want to have the return value in a
              different format. Could return an array slice, for example, ready for
              insertion into an array.
        """

    def append(self, other: TissueABC):
        """Add new tissue data representing new cohorts."""

        # TODO? Checking for consistent elements

        # Append the carbon mass from the incoming instance
        self.carbon_mass = np.append(self.carbon_mass, other.carbon_mass)

        # Append the element masses from the incoming instance
        for elem_name, elem_instance in self.element_masses.items():
            elem_instance.append(other.element_masses[elem_name])

    # @abstractmethod
    # def add_cohort(
    #     self,
    #     stem_allometry: StemAllometry,
    #     extra_pft_traits: ExtraTraitsPFT,
    #     new_pft_name: str,
    #     element: str,
    #     cohort: int,
    #     stem_traits: StemTraits,
    # ) -> None:
    #     """Add a cohort to the tissue type.

    #     Args:
    #         stem_allometry: The stem allometry object for the cohort.
    #         extra_pft_traits: Additional traits specific to the plant functional type.
    #         new_pft_name: The name of the new plant functional type.
    #         element: The name of the element (e.g., "N" for nitrogen).
    #         cohort: The index of the cohort to add.
    #         stem_traits: The stem traits for the cohort.
    #     """


@dataclass
class FoliageTissue(TissueABC):
    """A class to hold foliage stoichiometry data for a set of plant cohorts."""

    tissue_name = "foliage"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageTissue based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        for elem in with_elements:
            ideal_ratio = np.array(
                [
                    extra_pft_traits.traits[name][f"foliage_c_{elem.lower()}_ratio"]
                    for name in pft_names
                ]
            )
            turnover_ratio = np.array(
                [
                    extra_pft_traits.traits[name][
                        f"leaf_turnover_c_{elem.lower()}_ratio"
                    ]
                    for name in pft_names
                ]
            )

            element_masses[elem] = Element(
                name=elem,
                ideal_ratio=ideal_ratio,
                actual_element_mass=community.stem_allometry.foliage_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=community.stem_allometry.foliage_mass.copy(),
            community=community,
            element_masses=element_masses,
        )

    def elements_needed_for_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element quantity needed for growth for foliage tissue.

        Returns:
            The element quantity needed for growth for foliage tissue.
        """
        return {
            ky: (allocation.delta_foliage_mass * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def tissue_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """
        return {
            ky: (
                (allocation.foliage_turnover * (1 / elem.turnover_ratio)).squeeze()
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def extract_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """

        elemental_turnovers = self.tissue_turnover(allocation=allocation)

        self.carbon_mass -= allocation.foliage_turnover

        for ky, elem in self.element_masses.items():
            elem.actual_element_mass -= elemental_turnovers[ky]

        return {"C": allocation.foliage_turnover, **elemental_turnovers}

    # def add_cohort(
    #     self,
    #     stem_allometry: StemAllometry,
    #     extra_pft_traits: ExtraTraitsPFT,
    #     new_pft_name: str,
    #     element: str,
    #     cohort: int,
    #     stem_traits: StemTraits,
    # ) -> None:
    #     """Add a cohort to the foliage tissue type.

    #     Args:
    #         stem_allometry: The stem allometry object for the cohort.
    #         extra_pft_traits: Additional traits specific to the plant functional type.
    #         new_pft_name: The name of the new plant functional type.
    #         element: The name of the element (e.g., "N" for nitrogen).
    #         cohort: The index of the cohort to add.
    #         stem_traits: The stem traits for the cohort.
    #     """

    #     self.turnover_ratio = np.append(
    #         self.turnover_ratio,
    #         extra_pft_traits.traits[new_pft_name][
    #             f"leaf_turnover_c_{element.lower()}_ratio"
    #         ],
    #     )
    #     self.actual_element_mass = np.append(
    #         self.actual_element_mass, stem_allometry.foliage_mass[0][cohort]
    #     )
    #     self.ideal_ratio = np.append(
    #         self.ideal_ratio,
    #         extra_pft_traits.traits[new_pft_name][
    #               f"foliage_c_{element.lower()}_ratio"
    #         ],
    #     )


@dataclass
class ReproductiveTissue(TissueABC):
    """Holds reproductive tissue stoichiometry data for a set of plant cohorts."""

    tissue_name = "reproductive"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageTissue based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        for elem in with_elements:
            ideal_ratio = np.array(
                [
                    extra_pft_traits.traits[name][
                        f"plant_reproductive_tissue_turnover_c_{elem.lower()}_ratio"
                    ]
                    for name in pft_names
                ]
            )
            # Turnover ratio is identical to ideal ratio
            turnover_ratio = ideal_ratio

            element_masses[elem] = Element(
                name=elem,
                ideal_ratio=ideal_ratio,
                actual_element_mass=community.stem_allometry.reproductive_tissue_mass
                / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=community.stem_allometry.reproductive_tissue_mass,
            community=community,
            element_masses=element_masses,
        )

    def elements_needed_for_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element quantity needed for growth for foliage tissue.

        Returns:
            The element quantity needed for growth for foliage tissue.
        """
        return {
            ky: (
                allocation.delta_foliage_mass
                * self.community.stem_traits.p_foliage_for_reproductive_tissue
                * (1 / elem.ideal_ratio)
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def tissue_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """

        # TODO: Caching locally to avoid calling the property constructor twice - maybe
        #       this should a cached property?
        cx_ratios = self.Cx_ratio

        return {
            ky: (
                (
                    allocation.reproductive_tissue_turnover * (1 / cx_ratios[ky])
                ).squeeze()
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def extract_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """

        elemental_turnovers = self.tissue_turnover(allocation=allocation)

        self.carbon_mass -= allocation.reproductive_tissue_turnover

        for ky, elem in self.element_masses.items():
            elem.actual_element_mass -= elemental_turnovers[ky]

        return {"C": allocation.reproductive_tissue_turnover, **elemental_turnovers}

    # def add_cohort(
    #     self,
    #     stem_allometry: StemAllometry,
    #     extra_pft_traits: ExtraTraitsPFT,
    #     new_pft_name: str,
    #     element: str,
    #     cohort: int,
    #     stem_traits: StemTraits,
    # ) -> None:
    #     """Add a cohort to the reproductive tissue type.

    #     Args:
    #         stem_allometry: The stem allometry object for the cohort.
    #         extra_pft_traits: Additional traits specific to the plant functional type.
    #         new_pft_name: The name of the new plant functional type.
    #         element: The name of the element (e.g., "N" for nitrogen).
    #         cohort: The index of the cohort to add.
    #         stem_traits: The stem traits for the cohort.
    #     """
    #     self.actual_element_mass = np.append(
    #         self.actual_element_mass,
    #         stem_allometry.reproductive_tissue_mass[0][cohort],
    #     )
    #     self.ideal_ratio = np.append(
    #         self.ideal_ratio,
    #         extra_pft_traits.traits[new_pft_name][
    #             f"plant_reproductive_tissue_turnover_c_{element.lower()}_ratio"
    #         ],
    #     )


@dataclass
class WoodTissue(TissueABC):
    """A class to hold wood stoichiometry data for a set of plant cohorts."""

    tissue_name = "wood"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of WoodTissue based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        for elem in with_elements:
            ideal_ratio = np.array(
                [
                    extra_pft_traits.traits[name][f"deadwood_c_{elem.lower()}_ratio"]
                    for name in pft_names
                ]
            )
            turnover_ratio = np.zeros_like(ideal_ratio)

            element_masses[elem] = Element(
                name=elem,
                ideal_ratio=ideal_ratio,
                actual_element_mass=community.stem_allometry.stem_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=community.stem_allometry.stem_mass,
            community=community,
            element_masses=element_masses,
        )

    def elements_needed_for_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element quantity needed for growth for foliage tissue.

        Returns:
            The element quantity needed for growth for foliage tissue.
        """
        return {
            ky: (allocation.delta_stem_mass * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def tissue_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """
        return {
            ky: np.zeros_like(self.carbon_mass)
            for ky, elem in self.element_masses.items()
        }

    def extract_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for stem tissue.

        There is no turnover in stem tissue through time.

        Returns:
            The element quantities lost to turnover from stem tissue.
        """

        elemental_turnovers = self.tissue_turnover(allocation=allocation)

        return {"C": np.zeros_like(self.carbon_mass), **elemental_turnovers}

    # def add_cohort(
    #     self,
    #     stem_allometry: StemAllometry,
    #     extra_pft_traits: ExtraTraitsPFT,
    #     new_pft_name: str,
    #     element: str,
    #     cohort: int,
    #     stem_traits: StemTraits,
    # ) -> None:
    #     """Add a cohort to the wood tissue type.

    #     Args:
    #         stem_allometry: The stem allometry object for the cohort.
    #         extra_pft_traits: Additional traits specific to the plant functional type.
    #         new_pft_name: The name of the new plant functional type.
    #         element: The name of the element (e.g., "N" for nitrogen).
    #         cohort: The index of the cohort to add.
    #         stem_traits: The stem traits for the cohort.
    #     """
    #     self.actual_element_mass = np.append(
    #         self.actual_element_mass, stem_allometry.stem_mass[0][cohort]
    #     )
    #     self.ideal_ratio = np.append(
    #         self.ideal_ratio,
    #         extra_pft_traits.traits[new_pft_name][
    #             f"deadwood_c_{element.lower()}_ratio"
    #         ],
    #     )


@dataclass
class RootTissue(TissueABC):
    """A class to hold root stoichiometry data for a set of plant cohorts."""

    tissue_name = "root"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageTissue based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        for elem in with_elements:
            ideal_ratio = np.array(
                [
                    extra_pft_traits.traits[name][
                        f"root_turnover_c_{elem.lower()}_ratio"
                    ]
                    for name in pft_names
                ]
            )
            turnover_ratio = np.ones_like(ideal_ratio)

            element_masses[elem] = Element(
                name=elem,
                ideal_ratio=ideal_ratio,
                actual_element_mass=community.stem_allometry.fine_root_mass
                / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=community.stem_allometry.fine_root_mass,
            community=community,
            element_masses=element_masses,
        )

    def elements_needed_for_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element quantity needed for growth for foliage tissue.

        Returns:
            The element quantity needed for growth for foliage tissue.
        """
        return {
            ky: (
                allocation.delta_foliage_mass
                * self.community.stem_traits.zeta
                * self.community.stem_traits.sla
                * (1 / elem.ideal_ratio)
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def tissue_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """

        cx_ratios = self.Cx_ratio

        return {
            ky: (
                (allocation.fine_root_turnover * (1 / cx_ratios[ky])).squeeze()
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

    def extract_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for fine root tissue.

        Returns:
            The element quantities lost to turnover from fine root tissue.
        """

        elemental_turnovers = self.tissue_turnover(allocation=allocation)

        self.carbon_mass -= allocation.fine_root_turnover

        for ky, elem in self.element_masses.items():
            elem.actual_element_mass -= elemental_turnovers[ky]

        return {"C": allocation.fine_root_turnover, **elemental_turnovers}

    # def add_cohort(
    #     self,
    #     stem_allometry: StemAllometry,
    #     extra_pft_traits: ExtraTraitsPFT,
    #     new_pft_name: str,
    #     element: str,
    #     cohort: int,
    #     stem_traits: StemTraits,
    # ) -> None:
    #     """Add a cohort to the root tissue type.

    #     Args:
    #         stem_allometry: The stem allometry object for the cohort.
    #         extra_pft_traits: Additional traits specific to the plant functional type.
    #         new_pft_name: The name of the new plant functional type.
    #         element: The name of the element (e.g., "N" for nitrogen).
    #         cohort: The index of the cohort to add.
    #         stem_traits: The stem traits for the cohort.
    #     """
    #     self.actual_element_mass = np.append(
    #         self.actual_element_mass,
    #         stem_allometry.foliage_mass[0][cohort]
    #         * stem_traits.zeta[cohort]
    #         * stem_traits.sla[cohort],
    #     )
    #     self.ideal_ratio = np.append(
    #         self.ideal_ratio,
    #         extra_pft_traits.traits[new_pft_name][
    #             f"root_turnover_c_{element.lower()}_ratio"
    #         ],
    #     )


@dataclass
class Biomasses(CohortMethods, PandasExporter):
    """A class holding biomasses for a set of plant cohorts and tissues.

    This class holds the current ratios across tissue type for a community object, which
    in essence is a series of cohorts. It acts in parallel with StemAllometry, a class
    attribute of Community.

    The class is designed to be element-agnostic, so it can be used for any element as
    required.
    """

    tissues: list[TissueABC]
    """Tissues for the associated cohorts."""
    community: Community
    """The community object that the stoichiometry is associated with."""
    element_surpluses: dict[str, NDArray[np.floating]] = field(init=False)
    """The surplus of the element per cohort."""
    extra_pft_traits: ExtraTraitsPFT
    """Additional traits specific to the plant functional types."""
    tissue_names: list[str] = field(init=False)
    """A list giving the name of each tissue."""
    elements: tuple[str, ...] = field(init=False)
    """A list of the elements recorded in each tissue."""

    def __post_init__(self) -> None:
        """Initialize the element surplus for each cohort."""

        # Check the elements being used
        elements = {tuple(tissue.element_masses.keys()) for tissue in self.tissues}

        if len(elements) > 1:
            raise ValueError(
                f"Tissues passed to StemBiomasses have different elements: {elements}"
            )

        # Store lists of tissue types and element names, used for indexing tissues.
        self.tissue_names = [t.tissue_name for t in self.tissues]
        self.elements = elements.pop()

        # Populate the whole individual elemental surpluses
        # TODO - should this populate from the tissues themselves. When this is from
        # default_init then these _will_ be zeros, but that isn't true of direct use of
        # the constructor. Is there ever a case we'd use the __init__ though?

        self.element_surplus = {
            elem: np.zeros(self.community.n_cohorts) for elem in self.elements
        }

    @classmethod
    def default_init(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
        tissues: list[type[TissueABC]],
    ):
        """Create an instance of StemStoichiometry from the PFT stoichiometry ratios.

        Args:
            community: The community object that the stoichiometry is associated with.
            extra_pft_traits: Additional traits specific to the plant functional type.
            with_elements: The name of the elements to be used in the biomass
                representation.
            tissues: A list of tissue models to be used.

        Returns:
            An instance of StemBiomasses with default tissues for the community.
        """

        # Generate the default tissues
        default_tissues: list[TissueABC] = [
            tissue.from_pft_default_ratios(
                community=community,
                extra_pft_traits=extra_pft_traits,
                with_elements=with_elements,
            )
            for tissue in tissues
        ]

        return cls(
            tissues=default_tissues,
            community=community,
            extra_pft_traits=extra_pft_traits,
        )

    @property
    def total_element_masses(self) -> dict[str, NDArray[np.floating]]:
        """Calculate the total element mass for each cohort.

        Returns:
            The total element mass for each cohort.
        """
        masses = [t.get_elemental_masses for t in self.tissues]
        return {ky: np.add.reduce([m[ky] for m in masses]) for ky in self.elements}

    @property
    def tissue_deficit(self) -> dict[str, NDArray[np.floating]]:
        """Calculate the total element deficits for each cohort.

        Returns:
            The element deficit for all cohorts.
        """
        deficits = [t.deficit for t in self.tissues]
        return {ky: np.add.reduce([d[ky] for d in deficits]) for ky in self.elements}

    def _adjust_surpluses(
        self, masses: dict[str, NDArray[np.floating]], increase: bool = True
    ) -> None:
        """Adjust the element surpluses in the biomass object."""
        for elem in self.elements:
            if increase:
                self.element_surplus[elem] += masses[elem]
            else:
                self.element_surplus[elem] -= masses[elem]

    def account_for_growth(self, allocation: StemAllocation) -> None:
        """Distribute the element needed for growth to each tissue type.

        This method updates the actual element mass for each tissue type based on the
        element needed for growth calculated from the allocation.

        Args:
            allocation: The allocation object containing the growth allocation data.
        """

        for tissue in self.tissues:
            needed = tissue.elements_needed_for_growth(allocation)
            tissue.add_elemental_masses(needed)
            self._adjust_surpluses(needed, increase=False)

    def account_for_element_loss_turnover(self, allocation: StemAllocation) -> None:
        """Calculate the total element lost to turnover for each cohort.

        Elements are lost from the tree in the form of turnover, and so an equivalent
        amount of that element is required to replace what was lost. To represent this
        process, the element is allocated from the surplus store in the same quantity
        as turnover. This uses current ratios so that the C:x ratios are maintained.

        .. NOTE:

            These values are not subtracted from the element mass itself, as we assume
            that the tree regrows the lost tissue in the same timestep. This means that
            the element mass SHOULD stay the same, however the plant must have enough
            surplus to cover the loss - hence only subtracting from the element surplus.

        """
        for tissue in self.tissues:
            self._adjust_surpluses(tissue.tissue_turnover(allocation), increase=False)

    def balance_elements(self) -> None:
        """Redistribute elemental mass across tissues and element pool.

        This method calculates the elemental deficits and surpluses in each tissue and
        the central pool and then redistributes elemental masses to distribute whole
        stem deficits and surpluses down to the tissue level.

        Typically the central biomass pools will be empty at the end of this process
        unless elemental surpluses exceed the masses needed to bring all of tissues up
        to their ideal ratio.
        """

        # Get 3D arrays of elements/cohorts/tissue for actual element masses and
        # per tissue element deficits
        tissue_element_masses = np.stack([t.as_array() for t in self.tissues])
        tissue_element_deficits = np.stack(
            [t.as_array(deficit=True) for t in self.tissues]
        )

        # Get a 2D array of elements/cohort from the individual-level element pool
        stem_pools = np.stack(list(self.element_surplus.values()))

        # Calculate the redistribution of pool deficits (negative values) to tissues
        # weighted by the relative elemental mass for each tissue.
        pool_deficits_to_tissues = stem_pools * (
            tissue_element_masses / tissue_element_masses.sum(axis=0)
        )

        # Calculate the redistribution of pool surpluses (positive values) to tissues
        # weighted by their relative deficits. This will be np.nan if an element within
        # a tissue is _at_ the ideal ratio.
        tissue_relative_deficits = (
            tissue_element_deficits / tissue_element_deficits.sum(axis=0)
        )
        tissue_relative_deficits = np.where(
            np.isnan(tissue_relative_deficits), 0, tissue_relative_deficits
        )

        pool_surpluses_to_tissues = stem_pools * tissue_relative_deficits

        # Constrain element changes
        # - don't fill tissue deficits beyond the ideal ratio.
        pool_surpluses_to_tissues = np.minimum(
            tissue_element_deficits, pool_surpluses_to_tissues
        )
        # - don't drain tissues below zero.
        pool_deficits_to_tissues = np.maximum(
            -tissue_element_masses, pool_deficits_to_tissues
        )

        # Combine the two redistribution paths to give deficits and surpluses
        pool_to_tissue = np.where(
            stem_pools < 0, pool_deficits_to_tissues, pool_surpluses_to_tissues
        )

        # Allocate resulting masses back to tissues
        for tissue, to_tissue in zip(self.tissues, pool_to_tissue):
            tissue.add_elemental_masses(
                {ky: mass for ky, mass in zip(self.elements, to_tissue)}
            )

        # Remove masses allocated to tissues from pool.
        for elem, from_pool in zip(self.elements, pool_to_tissue.sum(axis=0)):
            self.element_surplus[elem] -= from_pool

    def get_tissue(self, tissue_type: str) -> TissueABC:
        """Get the tissue model for a specific tissue type.

        Args:
            tissue_type: The type of tissue to retrieve (e.g., 'foliage', 'wood').

        Returns:
            The tissue model corresponding to the specified tissue type.
        """

        try:
            return self.tissues[self.tissue_names.index(tissue_type)]
        except ValueError:
            raise ValueError(f"Tissue type '{tissue_type}' not found.")

    def append(self, other: Biomasses):
        """Append data from another Biomasses instance representing new cohorts."""

        # TODO check tissues and elements?

        for tissue_name in self.tissue_names:
            self.get_tissue(tissue_name).append(other.get_tissue(tissue_name))

        for elem in self.elements:
            self.element_surplus[elem] = np.append(
                self.element_surplus[elem], other.element_surplus[elem]
            )

    # def add_cohorts(
    #     self,
    #     new_cohort_data: Cohorts,
    #     flora: Flora,
    # ) -> None:
    #     """Add a set of new cohorts to the Biomasses model.

    #     TODO: currently using default ratios.

    #     Args:
    #         new_cohort_data: Cohort object containing information about the new
    #             cohort.
    #         flora: The flora object providing stem traits for the new cohort.
    #         element: The name of the element (e.g., "N" for nitrogen).
    #     """

    #     new_stem_traits = flora.get_stem_traits(pft_names=new_cohort_data.pft_names)
    #     new_stem_allometry = StemAllometry(
    #         stem_traits=new_stem_traits, at_dbh=new_cohort_data._dbh_values
    #     )

    #     for i in range(new_cohort_data.n_cohorts):
    #         for tissue in self.tissues:
    #             tissue.add_cohort(
    #                 stem_allometry=new_stem_allometry,
    #                 extra_pft_traits=self.extra_pft_traits,
    #                 new_pft_name=new_cohort_data.pft_names[i],
    #                 element=element,
    #                 cohort=i,
    #                 stem_traits=new_stem_traits,
    #             )

    #         self.element_surplus = np.append(self.element_surplus, 0.0)
