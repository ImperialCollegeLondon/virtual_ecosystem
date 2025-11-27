"""The subcanopy module provides a representation of subcanopy biomass as two pools. The
first is a pool of subcanopy vegetation, implemented as layer of pure leaf tissue in the
surface layer of the model vertical structure. The second is a pool of subcanopy
seedbank biomass.

Both pools use a simplified stiochiometric system: this is defined independently of the
:mod:`virtual_ecosystem.models.plants.stoichiometry` module, as that class explicitly
handles communities of cohorts with multiple tissue types. The subcanopy has much
simpler structure with two stoichiometric masses per grid cell and so the dynamics are
more easily handled by a separate implementation.

The module implements the following classes:

* The :class:`Nutrient` class provides a representation of nutrient masses per grid
  cell.
* The :class:`SubcanopyBiomass` class then tracks the carbon mass and an associated set
  of nutrient masses for a given pool.
* The :class:`Subcanopy` then maintains subcanopy biomass pools for the vegetation and
  seedbank and provides methods to update the light gathering and ecological dynamics of
  the subcanopy at each update step.

"""  # noqa:  D205

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst
from xarray import DataArray, full_like

from virtual_ecosystem.core.core_components import ModelTiming
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.plants.model_config import PlantsConstants


@dataclass
class Nutrient:
    """Dataclass for subcanopy elemental nutrient details.

    Args:
        name: The elemental nutrient name
        ideal_ratio: The ideal ratio for subcanopy tissue of the nutrient
        values: An array of per-grid-cell values
    """

    name: str
    ideal_ratio: float
    masses: NDArray[np.floating]

    @classmethod
    def from_constants(
        cls,
        tissue_name: str,
        element: str,
        constants: PlantsConstants,
        masses: NDArray[np.floating],
    ) -> Nutrient:
        """Factory method for Nutrient instances from the ideal ratio in constants.

        Args:
            tissue_name: The tissue name used in the plant constants
            element: The element name
            constants: A PlantConstants instance
            masses: The carbon biomasses of cells for the tissue.
        """

        ideal_ratio = getattr(constants, f"{tissue_name}_c_{element}_ratio")
        return cls(name=element, ideal_ratio=ideal_ratio, masses=masses / ideal_ratio)


SubcanopyNutrients: TypeAlias = dict[str, Nutrient]
"""A type to indicate a dictionary of Nutrient instances."""


class SubcanopyBiomass:
    """A stochiometric biomass class for Subcanopy vegetation.

    The class tracks the carbon and elemental nutrient masses across an array of grid
    cells and provides properties to report the nutrient ratios. It also provides
    methods to add and remove masses from the class and to remove excess nutrients above
    ideal ratios.
    """

    def __init__(
        self,
        carbon_mass: NDArray[np.floating],
        nutrients: SubcanopyNutrients,
    ) -> None:
        # Store Init arguments
        self.carbon_mass: NDArray[np.floating] = carbon_mass
        self.nutrients: SubcanopyNutrients = nutrients

    def __repr__(self) -> str:
        """Simple representation of class."""
        return f"SubcanopyBiomass(carbon={self.carbon_mass})"

    @classmethod
    def from_constants(
        cls,
        tissue_name: str,
        elements: tuple[str, ...],
        constants: PlantsConstants,
        masses: NDArray[np.floating],
    ) -> SubcanopyBiomass:
        """Factory method to generate a SubcanopyBiomass object from constants.

        The returned instance uses the provided carbon masses and initialises the named
        element masses at the ideal ratios set in the constants.
        """

        nutrients = {
            elem: Nutrient.from_constants(
                tissue_name=tissue_name,
                element=elem,
                constants=constants,
                masses=masses,
            )
            for elem in elements
        }

        return cls(carbon_mass=masses, nutrients=nutrients)

    def c_x_ratio(self, nutrient: str) -> NDArray[np.floating]:
        """Return the current CN ratio for the biomass."""
        return self.carbon_mass / self.nutrients[nutrient].masses

    def remove_mass_fraction(
        self, mass_fraction: float | NDArray[np.floating]
    ) -> SubcanopyBiomass:
        """Remove a proportion of the biomass.

        This function returns a new SubcanopyBiomass object containing the
        requested fraction of the carbon biomass. The removed carbon biomass is removed
        from the parent instance. The nitrogen and phosphorous masses are split using
        the same fraction to maintain the same CN and CP ratios.

        Args:
            mass_fraction: The proportion of mass to remove from each cell in the
                instance.
        """

        # Calculate extracted carbon and nutrient masses
        carbon_out = self.carbon_mass * mass_fraction

        nutrients_out = {
            nm: Nutrient(
                name=nm,
                ideal_ratio=nutr.ideal_ratio,
                masses=nutr.masses * mass_fraction,
            )
            for nm, nutr in self.nutrients.items()
        }

        # Remove masses from self
        self.carbon_mass -= carbon_out
        for nm in self.nutrients:
            self.nutrients[nm].masses -= nutrients_out[nm].masses

        return SubcanopyBiomass(carbon_mass=carbon_out, nutrients=nutrients_out)

    def add_mass(self, source: SubcanopyBiomass | SubcanopyNutrients):
        """Add biomass to a SubcanopyBiomass instance.

        The method adds carbon and nutrient biomasses (source is of type
        ``SubcanopyBiomass``) or just nutrient biomasses (source is of type
        ``SubcanopyNutrients``) to the calling instance.

        Args:
            source: The source ``SubcanopyBiomass`` or ``SubcanopyNutrients``
            instance.
        """

        # Add the carbon biomass and then drop down to just the nutrients
        if isinstance(source, SubcanopyBiomass):
            self.carbon_mass += source.carbon_mass
            source = source.nutrients

        for nm in source:
            self.nutrients[nm].masses += source[nm].masses

    def get_excess_nutrients(self) -> SubcanopyNutrients:
        """Extract excess nutrients.

        This method calculates the excess nitrogen and phosphorous biomass in a
        SubcanopyBiomass instance, given the provided ideal ratios. The method
        returns a SubcanopyNutrients instance containing excess nutrient masses: these
        will be be zero where the source biomass in a cell is at or below the ideal
        ratio.
        """

        # Subcanopy nutrients dictionary to return excesses
        excess_nutrients: SubcanopyNutrients = {}

        for nm, nutr in self.nutrients.items():
            # Calculate the excess for each nutrient, remove it from the instance mass
            # and add a corresponding Nutrient to the return value.
            excess = np.maximum(nutr.masses - (self.carbon_mass / nutr.ideal_ratio), 0)

            nutr.masses -= excess
            excess_nutrients[nm] = Nutrient(
                name=nm,
                ideal_ratio=nutr.ideal_ratio,
                masses=excess,
            )
        return excess_nutrients


class Subcanopy:
    """Representation of the subcanopy biomasses.

    This class maintains the representation of the subcanopy vegetation across grid
    cells within the Plants Model. The class maintains two biomass pools within each
    cell, the subcanopy vegetation and the seedbank for that vegetation, and tracks the
    carbon, nitrogen and phosphorous masses present in each pool.

    The class provides methods:

    * to calculate the leaf area index and fAPAR associated with the
      with the subcanopy, and
    * to calculate the dynamics of the subcanopy vegetation at each time step.

    Args:
        data: The model Data instance
        pyrealm_core_constants: The PModel core constants for the simulation.
        model_constants: The PlantModel constants for the simulation
        layer_index: The layer index of the surface layer in the vertical layer axis.
        model_timing: The core ModelTiming instance for the simulation.
    """

    elements: tuple[str, ...] = ("n", "p")
    """The set of nutrient elements currently tracked within the simulation."""

    def __init__(
        self,
        data: Data,
        pyrealm_core_constants: CoreConst,
        model_constants: PlantsConstants,
        layer_index: int,
        model_timing: ModelTiming,
    ) -> None:
        # Init attributes
        self.data: Data = data
        self.pyrealm_core_constants: CoreConst = pyrealm_core_constants
        self.model_constants: PlantsConstants = model_constants
        self.model_timing: ModelTiming = model_timing
        self.layer_index: int = layer_index

        # TODO: currently initialising from constants using ideal ratios but could load
        #       nutrient masses from init data.

        # Stochiometry of vegetation and seedbank
        self.vegetation_biomass: SubcanopyBiomass = SubcanopyBiomass.from_constants(
            masses=data["subcanopy_vegetation_biomass"].to_numpy(),
            elements=self.elements,
            tissue_name="subcanopy_vegetation",
            constants=self.model_constants,
        )

        self.seedbank_biomass: SubcanopyBiomass = SubcanopyBiomass.from_constants(
            masses=data["subcanopy_seedbank_biomass"].to_numpy(),
            elements=self.elements,
            tissue_name="subcanopy_seedbank",
            constants=self.model_constants,
        )

        # Type other attributes not populated at __init__
        self.lai: NDArray[np.floating]
        self.light_transmission: NDArray[np.floating]
        self.fapar: NDArray[np.floating]

    def calculate_dynamics(
        self,
        lue: NDArray[np.floating],
        iwue: NDArray[np.floating],
        swd: NDArray[np.floating],
    ) -> None:
        r"""Estimate the dynamics of subcanopy vegetation.

        This method models the biomass dynamics with the subcanopy vegetation and
        subcanopy seedbank pools during a model update.

        1. A fraction of the biomass in each pool is allocated to turnover, and passed
           into litter pools. The stoichiometric ratios of turnover biomass are
           identical to the pool biomasses.

        2. The predicted light use and intrinsic water use efficiencies (LUE and iWUE)
           in the surface layer are taken from the P Model and used to estimate gross
           primary productivity (GPP) and transpiration. GPP is reduced by respiration
           and yield to give net primary productivity NPP, which is added as new carbon
           biomass to the subcanopy vegetation. The soil dissolved nitrate, ammonium and
           phosphorous concentrations are then used to calculate the nutrient uptake
           associated with the transpiration volume and these are added to the subcanopy
           vegetation pool.

        3. A fraction of the subcanopy vegetation biomass is then removed to represent
           reproductive output to the seedbank pool. The stochiometric ratio of the
           reproductive biomass is initially identical to the vegetation biomass but any
           excess nitrogen and phosphorous above the configured ideal ratios is also
           transferred to the seedbank to represent seed provisioning.

        4. Lastly, new vegetative biomass is added from sprouting from the seedbank. The
           initial amount of sprouting biomass is set by the ``subcanopy_sprout_rate``
           constant but the contribution to subcanopy biomass is reduced using the
           ``subcanopy_sprout_yield`` constant. The remainder of the sprouting biomass
           is allocated to litter.

        .. TODO:: Timing of turnover
            The timing of turnover is going to affect growth patterns - it is currently
            placed right at the start of the dynamics, but it might be better to
            calculate an average biomass to spread turnover through the update period.
        """

        # Apply turnover for this update
        vegetation_turnover = self.vegetation_biomass.remove_mass_fraction(
            self.model_constants.subcanopy_vegetation_turnover
            / self.model_timing.updates_per_year
        )

        seedbank_turnover = self.seedbank_biomass.remove_mass_fraction(
            self.model_constants.subcanopy_vegetation_turnover
            / self.model_timing.updates_per_year
        )

        # Calculate the gross primary productivity since the last update.
        #    LUE                 1 layer          [gC mol-1]
        #    * canopy top SWD    1 layer          [µmol m-2 s-1]
        #    * subcanopy fapar   1 layer          [-]
        #    * DST to PPFD       scalar           [-]
        #    * time elapsed      scalar           [s]
        # Units:
        #    gC mol-1 * µmol m-2 s-1  * (-) * (-) * s = µg C m-2
        subcanopy_gpp = (
            lue
            * swd
            * self.fapar
            * self.model_constants.dsr_to_ppfd
            * self.model_timing.update_interval_seconds
        )

        # Calculate NPP, converting µg C m-2 to  kg C m-2
        # TODO - what is the fate of the (1- self.model_constants.subcanopy_yield). The
        #        assumption here is that it is lost to the atmosphere, but that is
        #        basically the same as respiration?
        subcanopy_npp = (
            self.model_constants.subcanopy_yield
            * (subcanopy_gpp * 1e-9)
            * (1 - self.model_constants.subcanopy_respiration_fraction)
        )

        # Transpiration and nutrient acquisition
        # - Calculate the transpiration associated with the GPP in moles
        self.subcanopy_transpiration = (
            subcanopy_gpp / (self.pyrealm_core_constants.k_c_molmass * 1e6)
        ) * iwue

        # Calculate the volume of water from µmol to m3 to convert soil water nutrient
        # concentrations in kg m3 into uptake nutrient mass.  Water has 1e6 g / 18.015 g
        # mol ~ 55509.2 moles per m3, so transpiration in µmol is (T * 1e-6) / (1e6 /
        # 18.015) = T * 1.8015e-11 metres cubed.
        subcanopy_volume_m3 = self.subcanopy_transpiration * 18.015e-11

        # Now calculate uptakes of nutrients through transpired water
        ammonium_uptake_kg = (
            subcanopy_volume_m3 * self.data["dissolved_ammonium"].to_numpy()
        )
        nitrate_uptake_kg = (
            subcanopy_volume_m3 * self.data["dissolved_nitrate"].to_numpy()
        )
        phosphorus_uptake_kg = (
            subcanopy_volume_m3 * self.data["dissolved_phosphorus"].to_numpy()
        )

        # TODO need to remove uptake from soil

        # Assimilate the gained masses into the vegetation first to update the
        # nutrient masses that are available for allocation to seedbank

        # TODO: Note that this section does not cleanly handle additional elements.
        self.vegetation_biomass.add_mass(
            SubcanopyBiomass(
                carbon_mass=subcanopy_npp,
                nutrients={
                    "n": Nutrient(
                        name="n",
                        ideal_ratio=self.model_constants.subcanopy_vegetation_c_n_ratio,
                        masses=ammonium_uptake_kg + nitrate_uptake_kg,
                    ),
                    "p": Nutrient(
                        name="p",
                        ideal_ratio=self.model_constants.subcanopy_vegetation_c_p_ratio,
                        masses=phosphorus_uptake_kg,
                    ),
                },
            )
        )

        # Extract the new carbon allocation for the seedbank using those new nutrient
        # ratios, catching cells with no vegetation biomass
        seedbank_carbon_fraction: NDArray[np.floating] = np.where(
            self.vegetation_biomass.carbon_mass > 0,
            subcanopy_npp
            * self.model_constants.subcanopy_reproductive_allocation
            / self.vegetation_biomass.carbon_mass,
            0,
        )

        seedbank_allocation = self.vegetation_biomass.remove_mass_fraction(
            mass_fraction=seedbank_carbon_fraction
        )

        # Extract seedbank provisioning using excess nutrients in vegetative biomass
        # TODO - how do these nutrients make it to the seedbank if there are excess
        #        nutrients but no carbon?
        seedbank_extra_nutrients = self.vegetation_biomass.get_excess_nutrients()

        # Get the new sprouted biomass from the seedbank during the time period
        sprouting_biomass = self.seedbank_biomass.remove_mass_fraction(
            self.model_constants.subcanopy_sprout_rate
            / self.model_timing.updates_per_year
        )

        # Remove the sprouting biomass yield losses from the total mass
        sprouting_yield_losses = sprouting_biomass.remove_mass_fraction(
            mass_fraction=1 - self.model_constants.subcanopy_sprout_yield
        )

        # Now allocate new biomasses to pools
        self.seedbank_biomass.add_mass(seedbank_allocation)
        self.seedbank_biomass.add_mass(seedbank_extra_nutrients)
        self.vegetation_biomass.add_mass(sprouting_biomass)
        seedbank_turnover.add_mass(sprouting_yield_losses)

        # Insert DataArrays with new values - could simply overwrite data but these
        # variables are created in the first update, so easier to just write afresh.
        coords = {"cell_id": self.data["cell_id"].data}

        # Write biomasses to Data
        biomasses: dict[str, SubcanopyBiomass] = {
            "subcanopy_vegetation": self.seedbank_biomass,
            "subcanopy_seedbank": self.seedbank_biomass,
            "subcanopy_vegetation_litter": vegetation_turnover,
            "subcanopy_seedbank_litter": seedbank_turnover,
        }

        for var, biomass in biomasses.items():
            self.data[f"{var}_biomass"] = DataArray(biomass.carbon_mass, coords=coords)

            for elem in self.elements:
                self.data[f"{var}_c_{elem}_ratio"] = DataArray(
                    biomass.c_x_ratio(elem), coords=coords
                )

        # Write lignin concentrations for litter components
        self.data["subcanopy_vegetation_litter_lignin"] = full_like(
            self.data["cell_id"], self.model_constants.subcanopy_vegetation_lignin
        )
        self.data["subcanopy_seedbank_litter_lignin"] = full_like(
            self.data["cell_id"], self.model_constants.subcanopy_seedbank_lignin
        )

        # Write nutrient uptakes and transpiration - one m3 is 1000 mm/m2
        for name, values in (
            ("subcanopy_ammonium_uptake", ammonium_uptake_kg),
            ("subcanopy_nitrate_uptake", nitrate_uptake_kg),
            ("subcanopy_phosphorus_uptake", phosphorus_uptake_kg),
            ("subcanopy_transpiration", subcanopy_volume_m3 / 1000),
        ):
            self.data[name] = DataArray(values, coords=coords)

    def set_light_capture(self, below_canopy_light_fraction: NDArray) -> None:
        r"""Calculate the leaf area index and absorption of subcanopy vegetation.

        The subcanopy vegetation is represented as pure leaf biomass (:math:`M_{SC}`, kg
        m-2), with an associated extinction coefficient (:math:`k`) and specific leaf
        area (:math:`\sigma`, kg m-2) set in the model constants. These can be used to
        calculate the leaf area index (:math:`L`) and hence the absorption fraction
        (:math:`f_{a}`) of  the subcanopy vegetation layer via the Beer-Lambert law: 

        .. math ::
            :nowrap:

            \[
                \begin{align*}
                    L &= M_{SC} \sigma \\
                    f_a = e^{-kL}
                \end{align*}
            \]
        """

        # Calculate the leaf area index - values are already in kg m-2 so no need to
        # account for the area occupied by the biomass - and set the leaf area
        self.lai = (
            self.data["subcanopy_vegetation_biomass"].to_numpy()
            * self.model_constants.subcanopy_specific_leaf_area
        )

        # Beer-Lambert transmission - note that this is 1 when there is no biomass and
        # so no light is absorbed by the vegetation and all of the subcanopy light
        # reaches the ground.
        self.light_transmission = np.exp(
            -self.model_constants.subcanopy_extinction_coef * self.lai
        )

        # Absorb a fraction of the below canopy light and pass the rest on to the ground
        # incident light fraction
        self.fapar = below_canopy_light_fraction * (1 - self.light_transmission)

        # Store those values
        self.data["leaf_area_index"][self.layer_index] = self.lai
        self.data["layer_fapar"][self.layer_index] = self.fapar
