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

FoliageBiomass:
    # Has different ratios in turnover mass

    biomass: foliage_mass
    turnover_biomass: foliage_turnover
    growth_biomass: delta_foliage_mass

    ideal_ratio: foliage_c_{elem.lower()}_ratio
    turnover_ratio: leaf_turnover_c_{elem.lower()}_ratio

    TODO - check to make sure turnover foliage doesn't get relatively _enriched_ if the
           plant is severely nutrient depleted.

ReproductiveBiomass:
    # Same ratios; has turnover

    biomass: reproductive_tissue_mass
    turnover_biomass: reproductive_tissue_turnover
    growth_biomass: foliage_tissue * p_foliage_for_reproductive_tissue

    ideal_ratio: not defined - identical to turnover ratio
    turnover_ratio: plant_reproductive_tissue_turnover_c_{elem.lower()}_ratio

RootBiomass:
    # Same ratios; has turnover

    biomass: fine_root_mass
    turnover_biomass: fine_root_turnover
    growth_biomass: delta_foliage_mass * zeta * sla

    ideal_ratio: not defined - identical to turnover ratio
    turnover_ratio: root_turnover_c_{elem.lower()}_ratio

StemBiomass
    # No turnover at present, so same ratios doesn't really make sense, but if there was
      turnover it probably would be at these ratios.

    biomass: stem_mass
    turnover_biomass: not defined, no stem turnover
    growth_biomass: delta_stem_mass

    ideal_ratio: deadwood_c_{elem.lower()}_ratio
    turnover_ratio: not defined (because there is no turnover)


TODO - factor out mass accessor functions (get_biomass etc) as in the lists above and
       then make those limited functions the abstract methods so that all the logic can
       be shared in base class methods.

TODO - make this all run on 2D CNP arrays (remove Element?) Have single arrays giving
       biomasses and ideal and turnover ratios.

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

from virtual_ecosystem.core.logger import LOGGER
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
class BiomassTissueABC(ABC):
    """A dataclass to hold tissue stoichiometry biomasses for a set of plant cohorts.

    This class holds the current quantity of a given element (generally N or P) for a
    specific plant tissue type (generally foliage, wood, roots or reproductive tissue).
    The class also holds the ideal ratio of the element for that tissue type. They hold
    an entry for each cohort in the data class.
    """

    tissue_name: ClassVar[str]
    """A tissue name for derived classes."""
    community: Community
    """The community object that the tissue is associated with."""
    extra_pft_traits: ExtraTraitsPFT
    # TODO: consider where best to store shared attributes like community.

    carbon_mass: NDArray[np.floating]
    """An 1D array of tissue carbon mass for each stem in cohorts in the community."""
    element_masses: dict[str, Element]
    """A dictionary of Elements containing nutrient masses each stem in cohorts in the
    community."""

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
    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase tissue biomasses following growth allocation for the tissue.

        This method should adjust the carbon biomass following the allocation model and
        similarly increase nutrient biomasses following the ideal ratios. The method
        must then also return the nutrient biomass increases, so that subsequent
        nutrient balancing can account for deficits and excesses within the stem.
        """

    @abstractmethod
    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the elemental losses to turnover for the tissue type.

        This method should return dictionary keyed by elements, including carbon. The
        values should be an array giving the per stem biomass within each cohort that is
        lost to turnover given the allocation.
        """

    def append(self, other: BiomassTissueABC):
        """Add new tissue data representing new cohorts."""

        # TODO? Checking for consistent elements

        # Append the carbon mass from the incoming instance
        self.carbon_mass = np.append(self.carbon_mass, other.carbon_mass)

        # Append the element masses from the incoming instance
        for elem_name, elem_instance in self.element_masses.items():
            elem_instance.append(other.element_masses[elem_name])


@dataclass
class FoliageBiomass(BiomassTissueABC):
    """A class to hold foliage stoichiometry data for a set of plant cohorts."""

    tissue_name = "foliage"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageBiomass based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        carbon_mass = community.stem_allometry.foliage_mass.squeeze()
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
                actual_element_mass=carbon_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=carbon_mass,
            extra_pft_traits=extra_pft_traits,
            community=community,
            element_masses=element_masses,
        )

    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase the biomasses of foliage tissue given the allocation model.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """
        self.carbon_mass += allocation.delta_foliage_mass.squeeze()

        nutrient_ideal_ratio_increase = {
            ky: (allocation.delta_foliage_mass * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """
        elemental_turnovers = {
            ky: (
                (allocation.foliage_turnover * (1 / elem.turnover_ratio)).squeeze()
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

        return {"C": allocation.foliage_turnover.squeeze(), **elemental_turnovers}


@dataclass
class ReproductiveBiomass(BiomassTissueABC):
    """Holds reproductive tissue stoichiometry data for a set of plant cohorts."""

    tissue_name = "plant_reproductive_tissue"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageBiomass based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        carbon_mass = community.stem_allometry.reproductive_tissue_mass.squeeze()

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
                actual_element_mass=carbon_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=carbon_mass,
            extra_pft_traits=extra_pft_traits,
            community=community,
            element_masses=element_masses,
        )

    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase the biomasses of reproductive tissue given the allocation model.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """

        carbon_increase = (
            allocation.delta_foliage_mass
            * self.community.stem_traits.p_foliage_for_reproductive_tissue
        )
        self.carbon_mass += carbon_increase.squeeze()

        nutrient_ideal_ratio_increase = {
            ky: (carbon_increase * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for reproductive tissue.

        Returns:
            The element quantity lost to turnover for reproductive tissue.
        """

        # TODO: Caching locally to avoid calling the property constructor for each
        # element  - maybe this should a cached property?

        cx_ratios = self.Cx_ratio

        elemental_turnovers = {
            ky: (
                (
                    allocation.reproductive_tissue_turnover * (1 / cx_ratios[ky])
                ).squeeze()
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

        LOGGER.debug(f"412: {cx_ratios!r}, {allocation.reproductive_tissue_turnover!r}")

        return {
            "C": allocation.reproductive_tissue_turnover.squeeze(),
            **elemental_turnovers,
        }


@dataclass
class FruitBiomass(BiomassTissueABC):
    """Holds fruit tissue stoichiometry data for a set of plant cohorts."""

    tissue_name = "fruit"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageBiomass based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        # Get the proportion of reproductive tissue allocated to fruit
        fruit_fraction = [
            extra_pft_traits.traits[name]["fruit_flesh_fraction"] for name in pft_names
        ]

        carbon_mass = (
            community.stem_allometry.reproductive_tissue_mass.squeeze() * fruit_fraction
        )

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
                actual_element_mass=carbon_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=carbon_mass,
            extra_pft_traits=extra_pft_traits,
            community=community,
            element_masses=element_masses,
        )

    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase the biomasses of reproductive tissue given the allocation model.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """

        fruit_fraction = [
            self.extra_pft_traits.traits[name]["fruit_flesh_fraction"]
            for name in self.community.cohorts.pft_names
        ]

        carbon_increase = (
            allocation.delta_foliage_mass
            * self.community.stem_traits.p_foliage_for_reproductive_tissue
            * fruit_fraction
        )
        self.carbon_mass += carbon_increase.squeeze()

        nutrient_ideal_ratio_increase = {
            ky: (carbon_increase * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for reproductive tissue.

        Returns:
            The element quantity lost to turnover for reproductive tissue.
        """

        # TODO: Caching locally to avoid calling the property constructor for each
        # element  - maybe this should a cached property?

        cx_ratios = self.Cx_ratio

        # Get the proportion of reproductive tissue allocated to fruit
        fruit_fraction = [
            1 - self.extra_pft_traits.traits[name]["fruit_flesh_fraction"]
            for name in self.community.cohorts.pft_names
        ]

        carbon_turnover = (
            allocation.reproductive_tissue_turnover.squeeze() * fruit_fraction
        )

        elemental_turnovers = {
            ky: ((carbon_turnover * (1 / cx_ratios[ky])).squeeze()).squeeze()
            for ky, elem in self.element_masses.items()
        }

        return {"C": carbon_turnover, **elemental_turnovers}


@dataclass
class SeedBiomass(BiomassTissueABC):
    """Holds fruit tissue stoichiometry data for a set of plant cohorts."""

    tissue_name = "seed"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageBiomass based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        # Get the proportion of reproductive tissue allocated to seed
        seed_fraction = [
            1 - extra_pft_traits.traits[name]["fruit_flesh_fraction"]
            for name in pft_names
        ]

        carbon_mass = (
            community.stem_allometry.reproductive_tissue_mass.squeeze() * seed_fraction
        )

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
                actual_element_mass=carbon_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=carbon_mass,
            extra_pft_traits=extra_pft_traits,
            community=community,
            element_masses=element_masses,
        )

    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase the biomasses of reproductive tissue given the allocation model.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """

        # Get the proportion of reproductive tissue allocated to seed
        seed_fraction = [
            1 - self.extra_pft_traits.traits[name]["fruit_flesh_fraction"]
            for name in self.community.cohorts.pft_names
        ]

        carbon_increase = (
            allocation.delta_foliage_mass
            * self.community.stem_traits.p_foliage_for_reproductive_tissue
            * seed_fraction
        )
        self.carbon_mass += carbon_increase.squeeze()

        nutrient_ideal_ratio_increase = {
            ky: (carbon_increase * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for reproductive tissue.

        Returns:
            The element quantity lost to turnover for reproductive tissue.
        """

        # TODO: Caching locally to avoid calling the property constructor for each
        # element  - maybe this should a cached property?

        cx_ratios = self.Cx_ratio

        # Get the proportion of reproductive tissue allocated to seed
        seed_fraction = [
            1 - self.extra_pft_traits.traits[name]["fruit_flesh_fraction"]
            for name in self.community.cohorts.pft_names
        ]

        carbon_turnover = (
            allocation.reproductive_tissue_turnover.squeeze() * seed_fraction
        )

        elemental_turnovers = {
            ky: ((carbon_turnover * (1 / cx_ratios[ky])).squeeze()).squeeze()
            for ky, elem in self.element_masses.items()
        }

        return {"C": carbon_turnover, **elemental_turnovers}


@dataclass
class StemBiomass(BiomassTissueABC):
    """A class to hold stem stoichiometry data for a set of plant cohorts."""

    tissue_name = "stem"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of WoodBiomass based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        carbon_mass = community.stem_allometry.stem_mass.squeeze()

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
                actual_element_mass=carbon_mass / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            carbon_mass=carbon_mass,
            extra_pft_traits=extra_pft_traits,
            community=community,
            element_masses=element_masses,
        )

    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase the biomasses of woody tissue given the allocation model.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """
        self.carbon_mass += allocation.delta_stem_mass.squeeze()

        nutrient_ideal_ratio_increase = {
            ky: (allocation.delta_stem_mass * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """
        elemental_turnovers = {
            ky: np.zeros_like(self.carbon_mass).squeeze()
            for ky, elem in self.element_masses.items()
        }

        return {"C": np.zeros_like(self.carbon_mass).squeeze(), **elemental_turnovers}


@dataclass
class RootBiomass(BiomassTissueABC):
    """A class to hold root stoichiometry data for a set of plant cohorts."""

    tissue_name = "root"

    @classmethod
    def from_pft_default_ratios(
        cls,
        community: Community,
        extra_pft_traits: ExtraTraitsPFT,
        with_elements: list[str],
    ):
        """Create a default instance of FoliageBiomass based on the PFT traits."""
        pft_names = community.cohorts.pft_names

        element_masses: dict[str, Element] = {}

        # until pyrealm 2.0.1
        fine_root_mass = (
            community.stem_allometry.foliage_mass
            * community.stem_traits.zeta
            * community.stem_traits.sla
        ).squeeze()

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
                actual_element_mass=fine_root_mass / ideal_ratio,
                # actual_element_mass=community.stem_allometry.fine_root_mass
                # / ideal_ratio,
                turnover_ratio=turnover_ratio,
            )

        return cls(
            # carbon_mass=community.stem_allometry.fine_root_mass,
            carbon_mass=fine_root_mass,
            extra_pft_traits=extra_pft_traits,
            community=community,
            element_masses=element_masses,
        )

    def apply_growth(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Increase the biomasses of root tissue given the allocation model.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """

        carbon_increase = (
            allocation.delta_foliage_mass
            * self.community.stem_traits.zeta
            * self.community.stem_traits.sla
        )

        self.carbon_mass += carbon_increase.squeeze()

        nutrient_ideal_ratio_increase = {
            ky: (carbon_increase * (1 / elem.ideal_ratio)).squeeze()
            for ky, elem in self.element_masses.items()
        }

        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Calculate the element mass lost to turnover for foliage tissue.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """

        cx_ratios = self.Cx_ratio

        elemental_turnovers = {
            ky: (
                (allocation.fine_root_turnover * (1 / cx_ratios[ky])).squeeze()
            ).squeeze()
            for ky, elem in self.element_masses.items()
        }

        return {"C": allocation.fine_root_turnover.squeeze(), **elemental_turnovers}


@dataclass
class Biomasses(CohortMethods, PandasExporter):
    """A class holding biomasses for a set of plant cohorts and tissues.

    This class holds the current ratios across tissue type for a community object, which
    in essence is a series of cohorts. It acts in parallel with StemAllometry, a class
    attribute of Community.

    The class is designed to be element-agnostic, so it can be used for any element as
    required.
    """

    tissues: list[BiomassTissueABC]
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

    # Note: these are hard-coded and must be updated if the simulation
    # uses different biomass classes.
    array_attrs: ClassVar[tuple[str, ...]] = (
        "biomass_foliage_carbon_mass",
        "biomass_foliage_n_actual_element_mass",
        "biomass_foliage_p_actual_element_mass",
        "biomass_fruit_carbon_mass",
        "biomass_fruit_n_actual_element_mass",
        "biomass_fruit_p_actual_element_mass",
        "biomass_seed_carbon_mass",
        "biomass_seed_n_actual_element_mass",
        "biomass_seed_p_actual_element_mass",
        "biomass_stem_carbon_mass",
        "biomass_stem_n_actual_element_mass",
        "biomass_stem_p_actual_element_mass",
        "biomass_root_carbon_mass",
        "biomass_root_n_actual_element_mass",
        "biomass_root_p_actual_element_mass",
    )
    """Array attribute names for all biomass tissue and element data."""

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
        tissues: list[type[BiomassTissueABC]],
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
        default_tissues: list[BiomassTissueABC] = [
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

    def apply_growth(self, allocation: StemAllocation) -> None:
        """Distribute the carbon allocated to growth and required nutrients to tissues.

        This method updates the actual biomasses for each tissue type based on the
        carbon allocation and elements needed for growth at ideal ratios, given that
        carbon biomass.

        The nutrient allocation is debited from the whole stem nutrient balance and
        subsequent nutrient balancing is responsible for adjusting tissue values to
        reflect nutrient excesses or deficits at the whole stem level.

        Args:
            allocation: The allocation object containing the growth allocation data.
        """

        for tissue in self.tissues:
            # Increase the tissue biomasses and record the nutrient masses required to
            # add that mass at ideal ratios.
            needed = tissue.apply_growth(allocation)
            # Record the nutrients biomasses at ideal ratios allocated to the tissue in
            # the whole stem balance.
            self._adjust_surpluses(needed, increase=False)

    def apply_turnover(
        self, allocation: StemAllocation
    ) -> dict[str, NDArray[np.floating]]:
        """Apply the effects of turnover on whole stem nutrient balances.

        This method takes a stem allocation object and returns an array per tissue of
        the carbon and nutrient biomasses of turnover from each pool.

        The calls to the individual `BiomassTissueABC.get_turnover` methods do not alter
        the biomasses in the tissue pools:

        * The carbon biomass turnover explicitly models the maintenance of tissue carbon
          biomass by replacement - an equal carbon biomass is lost to the environment

        * Nutrient biomasses are lost to turnover according to the turnover ratios. If
          the tissues are at their ideal ratio, then the elemental masses will not
          change. However, if the nutrient inputs within a timestep are not sufficient
          to maintain the current ratios of replacement tissue, then the tissue
          elemental masses should decrease. This is handled by recording the lost
          elemental masses in the stem-wide element surplus pools and balancing the
          accumulated deficits and gains to those pools at the end of the allocation
          process.

        TODO: This needs to account for herbivory - proportional to herbivory loss?

        Returns:
            A dictionary by tissue of turnover biomass arrays
        """

        # Get turnover by tissue
        turnover_by_tissue = {
            tissue.tissue_name: np.stack(list(tissue.get_turnover(allocation).values()))
            for tissue in self.tissues
        }

        # TODO - this next bit is clunky but moving the whole system over to arrays not
        #        dicts internally will probably fix it.

        # Accumulate the tissue specific turnovers into a single whole stem turnover
        total_turnover = np.add.reduce(list(turnover_by_tissue.values()))

        # This total is a CNP by cohorts array and needs to be split back to per element
        # dictionary of arrays.
        total_turnover_by_element = dict(zip(["C", *self.elements], total_turnover))
        self._adjust_surpluses(total_turnover_by_element, increase=False)

        return turnover_by_tissue

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
        # weighted by their relative deficits within the whole stem. This is problematic
        # when the whole stem deficit is zero (can be -inf, nan or inf depending on the
        # numerator), so explicitly handle zero stem deficits in a way that doesn't
        # raise warnings and sets the relative deficit to zero.

        stem_deficits = tissue_element_deficits.sum(axis=0)
        tissue_relative_deficits = np.divide(
            tissue_element_deficits,
            stem_deficits,
            out=np.zeros_like(tissue_element_deficits),
            where=stem_deficits != 0,
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

    def get_tissue(self, tissue_type: str) -> BiomassTissueABC:
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
