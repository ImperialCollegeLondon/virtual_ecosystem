"""The :mod:`~virtual_ecosystem.models.plants.biomasses` module contains structures
to track the realised stoichiometric biomasses of stems in the simulation. The
theoretical tissue masses for individuals in a cohort are derived from the T Model
predictions for the stem and growth and turnover are modelled using the GPP allocation
model from the T Model. However, the actual realised masses of different tissues can
differ from the theory due to herbivory and fruit production, so this class is used to
track the actual elemental masses realised by individuals through the simulation.

* The :class:`BiomassTissueABC` abstract base class and subclasses implementing
  biomasses for modelled plant tissues. The tissue biomass classes track the actual
  masses of carbon and elemental nutrients for stems in each cohort and provide methods
  to track changes elemental masses during tissue turnover, growth and herbivory.

* The :class:`Biomasses` class provides a wrapper around a set of tissues for cohorts,
  providing methods to initialise all tissues and handle turnover and growth across
  tissues. It also tracks the overall nutrient status of tissues and provides methods to
  balance nutrient requirements across tissues and track nutrient deficits and
  surpluses.

Both classes provide ``append`` methods to add new cohorts into the biomass
representation.
"""  # noqa: D205

from __future__ import annotations

from abc import ABC
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from pyrealm.demography.cohorts import Cohorts
from pyrealm.demography.tmodel import GrowthIncrements, StemAllocation, StemAllometry
from xarray import DataArray

from virtual_ecosystem.core.logger import LOGGER


def partition_reproductive_tissue_mass(
    cohorts: Cohorts, mass: NDArray[np.floating]
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Splits a reproductive tissue mass into fruit and seed components.

    This is used to split reproductive tissue mass, turnover or delta into fruit and
    seed components.

    Args:
        cohorts: A cohort dataframe providing trait data.
        mass: An array providing a reproductive tissue mass for each cohort.
    """

    fruit_mass = mass * cohorts["fruit_flesh_fraction"].to_numpy()
    return fruit_mass, mass - fruit_mass


class BiomassTissueABC(ABC):
    """Stoichiometry tissue biomasses for a set of plant cohorts.

    This base class holds the current elemental masses for a specific plant tissue (e.g.
    foliage, stem, fine roots) for a set of cohorts, along with the tissue-specicic
    ideal and turnover nutrient C/N ratios for each cohort.

    * The elemental biomasses are held as a numpy array with a column for each element
      and a row for each cohort. Carbon masses are always in the first column, followed
      by the nutrient elements given in the the ``elements`` class attribute. The
      initial biomasses are set using the allometric carbon mass of the tissue and the
      ideal ratios for the tissue, unless these are overridden by providing an array of
      ``initial_masses``.

    * The ideal and turnover ratios are also held as numpy arrays, with the same shape
      as the biomasses and are expressed as C/x ratios. The first column of these arrays
      is therefore C/C and is always equal to one.

    The class provides methods to add and remove biomasses through turnover, growth and
    herboivory and to add new cohorts to the biomass representation. It also has
    properties to access current realised C/x ratios and nutrient deficits.

    Subclasses of this abstract base class provide implementations for specific tissues
    and are defined simply by setting class attributes that give the names of tissue
    specific mass and ratio attributes from model objects:

    * ``tissue_name``: a tissue label
    * ``mass_attr``: the tissue mass attribute name in StemAllometry objects.
    * ``turnover_mass_attr``: the tissue turnover mass attribute name in StemAllocation
      objects.
    * ``growth_mass_attr``: The tissue growth mass attribute name in GrowthIncrements
      objects.
    * ``ideal_ratio_attrs``: A string that can be used to match the tissue ideal ratio
      attributes defined in the flora and included in Cohorts objects
    * ``turnover_ratio_attrs``: As above but matching tissue turnover ratio attributes.
      These will typically point to the same attribute as the ideal ratio - the tissue
      does not resorb nutrients during turnover - but can identify different ratios
      where resorption does occur.

    The last two attributes must be defined using the format ``stem_c_ELEM_ratio``,
    where ELEM can be be replaced with the lower case element letter to match the
    specific elemental ratio traits (e.g. ``stem_c_n_ratio``, ``stem_c_p_ratio``)

    Args:
        cohorts: A dataframe of cohort data.
        allometry: A StemAllometry object for the cohorts.
        initial_masses: An optional initial set of elemental biomasses.
    """

    tissue_name: ClassVar[str]
    """A tissue name for derived classes."""
    mass_attr: ClassVar[str]
    """The tissue mass attribute name in StemAllometry objects"""
    turnover_mass_attr: ClassVar[str]
    """The tissue turnover mass attribute name in StemAllocation objects"""
    growth_mass_attr: ClassVar[str]
    """The tissue growth mass attribute name in GrowthIncrements objects"""
    ideal_ratio_attrs: ClassVar[str]
    """The form of the tissue ideal ratio attributes defined in the flora and available 
    from Cohorts objects"""
    turnover_ratio_attrs: ClassVar[str]
    """The form of the tissue turnover ratio attributes defined in the flora and
    available from Cohorts objects"""

    elements: ClassVar[tuple[str, ...]] = ("N", "P")
    """A tuple giving the nutrient elements included in the biomasses."""

    def __init__(
        self,
        cohorts: Cohorts,
        allometry: StemAllometry,
        initial_masses: NDArray[np.floating] | None = None,
    ):
        """Create a default instance of Tissue based on the PFT traits."""

        # Need to use copy to avoid the biomass and allometry masses refer to the same
        # object!

        self.elemental_masses: NDArray[np.floating]
        """An 2D array of tissue elemental masses stems in cohorts."""

        self.turnover_ratios: NDArray[np.floating]
        """Elemental ratios for tissue turnover. These may be identical to ideal ratios 
        if the tissue does have nutrient resorption on turnover tissue."""

        self.ideal_ratios: NDArray[np.floating]
        """Ideal elemental ratios for the tissue."""

        self.set_ideal_ratios(cohorts=cohorts)
        self.set_turnover_ratios(cohorts=cohorts)

        if initial_masses is not None:
            if not initial_masses.shape == (len(cohorts), len(self.elements) + 1):
                raise ValueError(
                    "Shape of provided elemental masses not compatible with number "
                    "of cohorts and tracked nutrients."
                )
            self.elemental_masses = initial_masses
            return

        # Otherwise set from ideal ratios
        carbon_mass = getattr(allometry, self.mass_attr)
        self.elemental_masses = carbon_mass[:, None] / self.ideal_ratios

    def get_ratios(self, cohorts, ratio_attrs) -> NDArray[np.floating]:
        """Get an array of the ideal or turnover ratios for a tissue.

        Args:
            cohorts: The cohort data providing ratios
            ratio_attrs: The name form for the different elemental ratio attributes.
        """
        return np.stack(
            [
                np.ones(len(cohorts)),
                *[
                    cohorts[ratio_attrs.replace("ELEM", elem.lower())].to_numpy()
                    for elem in self.elements
                ],
            ],
            axis=1,
        )

    def set_ideal_ratios(self, cohorts: Cohorts) -> None:
        """Method to set ideal nutrient ratios."""
        self.ideal_ratios = self.get_ratios(
            cohorts=cohorts, ratio_attrs=self.ideal_ratio_attrs
        )

    def set_turnover_ratios(self, cohorts: Cohorts) -> None:
        """Abstract method to set turnover nutrient ratios."""
        self.turnover_ratios = self.get_ratios(
            cohorts=cohorts, ratio_attrs=self.turnover_ratio_attrs
        )

    @property
    def deficits(self) -> NDArray[np.floating]:
        """Calculate the elemental deficits (ideal mass - actual mass) for the tissue.

        Returns:
            The tissue deficits for the tissue.
        """
        return (
            self.elemental_masses[:, [0]] / self.ideal_ratios
        ) - self.elemental_masses

    @property
    def Cx_ratio(self) -> NDArray[np.floating]:
        """Get current carbon to element ratios for the tissue type.

        This has to handle cases where a tissue has no biomass at all or no actual
        elemental mass, which would otherwise generate NaN ratios (C/0). It explicitly
        sets these cases to infinity.

        .. TODO:

            Not currently used in the PlantsModel and anyway returned something odd.
            Updated to give current actual Cx ratios, but maybe can delete

        Returns:
            The carbon to element ratios for the tissue.
        """

        return np.where(
            self.elemental_masses == 0,
            np.inf,
            self.elemental_masses[:, [0]] / self.elemental_masses,
        )

    def add_elemental_masses(self, masses: NDArray[np.floating]) -> None:
        """Add elemental masses to the tissues."""

        if not self.elemental_masses.shape == masses.shape:
            raise ValueError("Error adding elements mass - incompatible shapes.")

        updated_masses = self.elemental_masses + masses
        # Clip any negative result from the update and log the values clipped.
        negative_updated = updated_masses < 0.0
        if np.any(negative_updated):
            LOGGER.warning(
                f"Clipping negative updated biomasses in "
                f"{self.tissue_name}: {updated_masses[negative_updated]}"
            )
        self.elemental_masses = np.clip(updated_masses, 0.0, None)

    def append(self, other: BiomassTissueABC):
        """Add new tissue data representing new cohorts."""

        for attr in ("elemental_masses", "ideal_ratios", "turnover_ratios"):
            # Append the elemental masses and ratios from the incoming instance
            # onto the existing instance.
            setattr(
                self, attr, np.concatenate([getattr(self, attr), getattr(other, attr)])
            )

    def get_turnover(self, allocation: StemAllocation) -> NDArray[np.floating]:
        """Calculate the biomass lost to turnover for foliage tissue.

        This method calculates the tissue turnover from the GPP allocation model and
        returns an array giving the biomasses lost to turnover. This does not alter the
        biomasses within the tissue as turnover biomass is replaced by GPP allocation.

        Returns:
            The element quantity lost to turnover for foliage tissue.
        """
        carbon_mass = getattr(allocation, self.turnover_mass_attr)

        return carbon_mass[:, None] / self.turnover_ratios

    def apply_growth(self, growth_increments: GrowthIncrements) -> NDArray[np.floating]:
        """Apply biomasses increases given growth increments.

        This method adjusts the carbon biomass following the growth increments from the
        allocation model and increases nutrient biomasses following the ideal ratios.
        The method returns the biomass increases, so that subsequent nutrient balancing
        can account for deficits and excesses across tissues.

        Returns:
            The increases in element quantities needed to support growth at the ideal
            ratio for the tissue.
        """
        carbon_mass = getattr(growth_increments, self.growth_mass_attr)
        nutrient_ideal_ratio_increase = carbon_mass[:, None] / self.ideal_ratios
        self.add_elemental_masses(nutrient_ideal_ratio_increase)

        return nutrient_ideal_ratio_increase

    def get_relative_carbon_biomass_by_pft(
        self, cohorts: Cohorts
    ) -> NDArray[np.floating]:
        """Get the proportional carbon biomass of each cohort within PFTs for a tissue.

        This is used to distribute herbivory - which happens at the PFT level - back
        down to individual cohorts, assuming that herbivory is distributed between
        cohorts of the same PFT in proportion to the available biomass.

        TODO: This will need to nest by cell id if we drop communities, since herbivory
              is applied at the cell level.

        Args:
            cohorts: The cohort data for the biomasses.

        Returns:
            An one-dimensional array with length equal to the number of cohorts giving
            the proportional carbon biomass of that cohort within the PFT.
        """

        carbon_mass = self.elemental_masses[:, 0]
        total_pft_carbon_biomass = np.zeros_like(carbon_mass)

        # Use boolean indexing to collate the total PFT biomass for each cohort
        for pft in set(cohorts["pft_name"]):
            # boolean index along carbon_mass array
            in_pft = cohorts["pft_name"].to_numpy() == pft
            # aggregate carbon masses across cohorts in the PFT and assign total.
            total_pft_carbon_biomass[in_pft] = carbon_mass[in_pft].sum()

        return carbon_mass / total_pft_carbon_biomass

    def apply_herbivory(self, herbivory_array: DataArray):
        """Remove biomass from a tissue to account for herbivory.

        The input is expected to be a DataArray with a pft dimension matching the number
        of cohorts and then an element dimension containing C and then each element.
        """
        self.elemental_masses -= herbivory_array.to_numpy()


class FoliageBiomass(BiomassTissueABC):
    """Foliage tissue stoichiometry biomasses for plant cohorts."""

    tissue_name = "foliage"
    mass_attr = "foliage_mass"
    turnover_mass_attr = "foliage_turnover"
    growth_mass_attr = "delta_foliage_mass"
    ideal_ratio_attrs = "foliage_c_ELEM_ratio"
    turnover_ratio_attrs = "leaf_turnover_c_ELEM_ratio"


class FruitBiomass(BiomassTissueABC):
    """Fruit tissue stoichiometry biomasses for plant cohorts."""

    tissue_name = "fruit"
    mass_attr = "fruit_mass"
    turnover_mass_attr = "fruit_turnover"
    growth_mass_attr = "delta_fruit_mass"
    ideal_ratio_attrs = "plant_reproductive_tissue_turnover_c_ELEM_ratio"
    turnover_ratio_attrs = "plant_reproductive_tissue_turnover_c_ELEM_ratio"


class SeedBiomass(BiomassTissueABC):
    """Seed tissue stoichiometry biomasses for plant cohorts."""

    tissue_name = "seed"
    mass_attr = "seed_mass"
    turnover_mass_attr = "seed_turnover"
    growth_mass_attr = "delta_seed_mass"
    ideal_ratio_attrs = "plant_reproductive_tissue_turnover_c_ELEM_ratio"
    turnover_ratio_attrs = "plant_reproductive_tissue_turnover_c_ELEM_ratio"


class StemBiomass(BiomassTissueABC):
    """Stem tissue stoichiometry biomasses for plant cohorts."""

    tissue_name = "stem"
    mass_attr = "stem_mass"
    turnover_mass_attr = "branch_turnover"
    growth_mass_attr = "delta_stem_mass"
    ideal_ratio_attrs = "deadwood_c_ELEM_ratio"
    turnover_ratio_attrs = "deadwood_c_ELEM_ratio"


class RootBiomass(BiomassTissueABC):
    """Fine root tissue stoichiometry biomasses for plant cohorts."""

    tissue_name = "root"
    mass_attr = "fine_root_mass"
    turnover_mass_attr = "fine_root_turnover"
    growth_mass_attr = "delta_fine_root_mass"
    ideal_ratio_attrs = "root_turnover_c_ELEM_ratio"
    turnover_ratio_attrs = "root_turnover_c_ELEM_ratio"


class Biomasses:  # TODO - ToDataFrameMixin? Some kind of export method
    """A class holding biomasses for a set of plant cohorts and tissues.

    This class holds the current ratios across tissue type for a community object, which
    in essence is a series of cohorts. It acts in parallel with StemAllometry, a class
    attribute of Community.

    The class is designed to be element-agnostic, so it can be used for any element as
    required.
    """

    # NOTE: these are hard-coded and must be updated if the simulation
    #       uses different biomass classes.
    # TODO: Might also be redundant if the ToDataFramMixin approach isn't going to be
    #       used, which it might well not be - can just concat the tissue arrays into a
    #       data frame.
    _array_attrs: ClassVar[tuple[str, ...]] = (
        "foliage_c_biomass",
        "foliage_n_biomass",
        "foliage_p_biomass",
        "fruit_c_biomass",
        "fruit_n_biomass",
        "fruit_p_biomass",
        "seed_c_biomass",
        "seed_n_biomass",
        "seed_p_biomass",
        "stem_c_biomass",
        "stem_n_biomass",
        "stem_p_biomass",
        "root_c_biomass",
        "root_n_biomass",
        "root_p_biomass",
    )
    """Array attribute names for all biomass tissue and element data."""

    def __init__(
        self,
        tissues: list[BiomassTissueABC],
        element_surpluses: NDArray[np.floating] | None = None,
    ) -> None:

        # TODO - do we actually need this constructor as opposed to just using the
        #        from_cohorts method as __init__?

        self.tissues: list[BiomassTissueABC] = tissues
        """Tissues for the associated cohorts."""
        self.element_surpluses: NDArray[np.floating]
        """The surplus of the element per cohort."""
        self.tissue_names: list[str]
        """A list giving the name of each tissue."""
        self.elements: tuple[str, ...]
        """A list of the elements recorded in each tissue."""

        # Check the elemental mass shapes are consistent
        element_shape_set = {t.elemental_masses.shape for t in self.tissues}

        if len(element_shape_set) > 1:
            raise ValueError(
                f"Tissues passed to StemBiomasses have different elemental "
                f"mass array shapes: {element_shape_set}"
            )
        element_shapes = element_shape_set.pop()

        # Check the elements being used
        elements = {t.elements for t in self.tissues}

        if len(elements) > 1:
            raise ValueError(
                f"Tissues passed to StemBiomasses have different elements: {elements}"
            )

        # Store lists of tissue types and element names, used for indexing tissues.
        self.tissue_names = [t.tissue_name for t in self.tissues]
        self.elements = elements.pop()

        # Populate the whole individual elemental surpluses
        if element_surpluses is not None:
            if element_surpluses.shape != element_shapes:
                raise ValueError(
                    "Provided element surpluses have a different shape to the tissue "
                    "biomass arrays."
                )
            self.element_surpluses = element_surpluses
        else:
            self.element_surpluses = np.zeros(element_shapes)

    @classmethod
    def from_cohorts(
        cls,
        cohorts: Cohorts,
        allometry: StemAllometry,
        tissues: list[type[BiomassTissueABC]],
    ):
        """Create a Biomasses instance from cohort data using the ideal element ratios.

        Args:
            cohorts: A data frame of cohorts providing trait data.
            allometry: The allometry of the cohorts.
            tissues: A list of tissue models to be used.

        Returns:
            An instance of Biomasses with default element ratios for the cohorts.
        """

        # Generate the default tissues
        default_tissues: list[BiomassTissueABC] = [
            tissue(
                cohorts=cohorts,
                allometry=allometry,
            )
            for tissue in tissues
        ]

        return cls(tissues=default_tissues)

    @property
    def total_element_masses(self) -> NDArray[np.floating]:
        """Calculate the total element mass for each cohort.

        Returns:
            The total element mass across tissues for each cohort.
        """
        return np.add.reduce([t.elemental_masses for t in self.tissues])

    @property
    def tissue_deficit(self) -> NDArray[np.floating]:
        """Calculate the total element deficits for each cohort.

        Returns:
            The element deficit for all cohorts.
        """

        return np.add.reduce([t.deficits for t in self.tissues])

    def _adjust_surpluses(
        self, masses=NDArray[np.floating], increase: bool = True
    ) -> None:
        """Adjust the element surpluses in the biomass object."""
        if increase:
            self.element_surpluses += masses
        else:
            self.element_surpluses -= masses

    def apply_growth(self, growth_increments: GrowthIncrements) -> None:
        """Distribute the carbon allocated to growth and required nutrients to tissues.

        This method updates the actual biomasses for each tissue type based on the
        carbon allocation and elements needed for growth at ideal ratios, given that
        carbon biomass.

        The nutrient allocation is debited from the whole stem nutrient balance and
        subsequent nutrient balancing is responsible for adjusting tissue values to
        reflect nutrient excesses or deficits at the whole stem level.

        Args:
            growth_increments: A GrowthIncrements instance containing the growth
                increment data.
        """

        for tissue in self.tissues:
            # Increase the tissue biomasses and record the nutrient masses required to
            # add that mass at ideal ratios.
            needed = tissue.apply_growth(growth_increments=growth_increments)
            # Record the nutrients biomasses at ideal ratios allocated to the tissue in
            # the whole stem balance, after zeroing carbon which is allocated from NPP.
            needed[:, 0] = 0
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

        Returns:
            A dictionary by tissue of turnover biomass arrays
        """

        # Get turnover by tissue
        turnover_by_tissue = {
            t.tissue_name: t.get_turnover(allocation) for t in self.tissues
        }

        # Accumulate the tissue specific turnovers into a single whole stem turnover
        total_turnover = np.add.reduce(list(turnover_by_tissue.values()))

        # Remove carbon from losses - replaced by turnover allocation - and update
        # surpluses
        total_turnover[:, 0] = 0
        self._adjust_surpluses(total_turnover, increase=False)

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
        tissue_element_masses = np.stack([t.elemental_masses for t in self.tissues])
        tissue_element_deficits = np.stack([t.deficits for t in self.tissues])

        # Calculate the redistribution of pool deficits (negative values) to tissues
        # weighted by the relative elemental mass for each tissue.
        #
        # This needs to guard against the pathological case where there is _none_ of the
        # element in any of the tissues for a cohort (which leads to divide by zero and
        # hence np.nan/np.inf). Values in this case are forced as zero - they can't have
        # more of that element removed since they have none.

        tissue_total_element_masses = tissue_element_masses.sum(axis=0)
        pool_deficits_to_tissues = self.element_surpluses * np.divide(
            tissue_element_masses,
            tissue_total_element_masses,
            out=np.zeros_like(tissue_element_masses),
            where=tissue_total_element_masses > 0,
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

        pool_surpluses_to_tissues = self.element_surpluses * tissue_relative_deficits

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
            self.element_surpluses < 0,
            pool_deficits_to_tissues,
            pool_surpluses_to_tissues,
        )

        # Allocate resulting masses back to tissues
        for tissue, to_tissue in zip(self.tissues, pool_to_tissue):
            tissue.add_elemental_masses(to_tissue)

        # Remove masses allocated to tissues from pool.
        self.element_surpluses -= pool_to_tissue.sum(axis=0)

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

        self.element_surpluses = np.concatenate(
            [
                self.element_surpluses,
                other.element_surpluses,
            ]
        )
