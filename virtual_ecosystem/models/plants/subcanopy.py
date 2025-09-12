"""The subcanopy module provides blah blah blah

This is :class:`SubcanopyBiomass` is defined independently of the
:mod:`virtual_ecosystem.models.plants.stochiometry` module, as that class explicitly
handles communities of cohorts with multiple tissue types. The subcanopy has much
simpler structure with two stoichiometric masses per grid cell and so the dynamics are
more easily handled by a separate implementation.

.. NOTE::

This currently hardcodes the specific nutrients. If this expands beyond N and P, see the
discussion here: https://github.com/ImperialCollegeLondon/virtual_ecosystem/pull/1032

"""  # noqa: D415

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst
from pyrealm.pmodel import PModel

from virtual_ecosystem.core.core_components import ModelTiming
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.plants.constants import PlantsConsts


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
        constants: PlantsConsts,
        masses: NDArray[np.floating],
    ) -> Nutrient:
        """Factory method for Nutrient instances from the ideal ratio in constants.

        Args:
            tissue_name: The tissue name used in the plant constants
            element: The element name
            constants: A PlantConsts instance
            masses: The carbon biomasses of cells for the tissue.
        """

        ideal_ratio = getattr(PlantsConsts, f"{tissue_name}_c_{element}_ratio")
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

    def c_x_ratio(self, nutrient: str) -> NDArray[np.floating]:
        """Return the current CN ratio for the biomass."""
        return self.carbon_mass / self.nutrients[nutrient].masses

    def remove_mass_fraction(self, mass_fraction: float) -> SubcanopyBiomass:
        """Remove a proportion of the biomass.

        This function returns a new SubcanopyBiomass object containing the
        requested fraction of the carbon biomass. The removed carbon biomass is removed
        from the parent instance. The nitrogen and phosphorous masses are split using
        the same fraction to maintain the same CN and CP ratios.

        Args:
            mass_fraction: The proportion of mass to remove from the instance.
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
            self.nutrients[nm].masses -= source[nm].masses

    def get_excess_nutrients(self) -> SubcanopyNutrients:
        """Extract excess nutrients.

        This method calculates the excess nitrogen and phosphorous biomass in a
        SubcanopyBiomass instance, given the provided ideal ratios. The method
        returns a SubcanopyNutrients instance containing excess nutrient masses: these
        will be be zero where the source biomass in a cell is at or below the ideal
        ratio.
        """

        return {
            nm: Nutrient(
                name=nm,
                ideal_ratio=nutr.ideal_ratio,
                masses=np.maximum(
                    nutr.masses - (self.carbon_mass / nutr.ideal_ratio), 0
                ),
            )
            for nm, nutr in self.nutrients.items()
        }


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
        pmodel_core_constants: The PModel core constants for the simulation.
        model_constants: The PlantModel constants for the simulation
        layer_index: The layer index of the surface layer in the vertical layer axis.
        model_timing: The core ModelTiming instance for the simulation.
    """

    elements: tuple[str, ...] = ("n", "p")
    """The set of nutrient elements currently tracked within the simulation."""

    def __init__(
        self,
        data: Data,
        pmodel_core_constants: CoreConst,
        model_constants: PlantsConsts,
        layer_index: int,
        model_timing: ModelTiming,
    ) -> None:
        # Init attributes
        self.data: Data = data
        self.pmodel_core_constants: CoreConst = pmodel_core_constants
        self.model_constants: PlantsConsts = model_constants
        self.model_timing: ModelTiming = model_timing
        self.layer_index: int = layer_index

        # TODO: currently initialising from constants using ideal ratios but could load
        #       nutrient masses from init data.

        # Stochiometry of vegetation and seedbank
        vegetation_mass = data["subcanopy_vegetation_biomass"].to_numpy()

        vegetation_nutrients: SubcanopyNutrients = {
            elem: Nutrient.from_constants(
                tissue_name="subcanopy_vegetation",
                element=elem,
                constants=self.model_constants,
                masses=vegetation_mass,
            )
            for elem in self.elements
        }

        self.vegetation_biomass: SubcanopyBiomass = SubcanopyBiomass(
            carbon_mass=vegetation_mass, nutrients=vegetation_nutrients
        )

        seedbank_mass = data["subcanopy_seedbank_biomass"].to_numpy()

        # Generate accompanying nutrients
        seedbank_nutrients: SubcanopyNutrients = {
            elem: Nutrient.from_constants(
                tissue_name="subcanopy_seedbank",
                element=elem,
                constants=self.model_constants,
                masses=seedbank_mass,
            )
            for elem in self.elements
        }

        self.seedbank_biomass: SubcanopyBiomass = SubcanopyBiomass(
            carbon_mass=seedbank_mass, nutrients=seedbank_nutrients
        )

        # Type other attributes not populated at __init__
        self.lai: NDArray[np.floating]
        self.light_transmission: NDArray[np.floating]
        self.fapar: NDArray[np.floating]

    def calculate_dynamics(self, pmodel: PModel) -> None:
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
        #    LUE                     1 layer          [gC mol-1]
        #    * shortwave absorption  1 layer          [µmol m-2 s-1]
        #    * DST to PPFD           scalar           [-]
        #    * time elapsed     scalar                [s]
        # Units:
        #    gC mol-1 * µmol m-2 s-1  * (-) * s = µg C m-2
        subcanopy_gpp = (
            pmodel.lue[self.layer_index, :]
            * self.data["shortwave_absorption"][self.layer_index, :]
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
            subcanopy_gpp / (self.pmodel_core_constants.k_c_molmass * 1e6)
        ) * pmodel.iwue[self.layer_index, :]

        # Calculate the volume of water from µmol to m3 to convert soil water nutrient
        # concentrations in kg m3 into uptake nutrient mass.  Water has 1e6 g / 18.015 g
        # mol ~ 55509.2 moles per m3, so transpiration in µmol is (T * 1e-6) / (1e6 /
        # 18.015) = T * 1.8015e-11 metres cubed.
        subcanopy_volume_m3 = self.subcanopy_transpiration * 18.015e-11

        # Now calculate uptakes of nutrients through transpired water
        ammonium_uptake_kg = subcanopy_volume_m3 * self.data["dissolved_ammonium"]
        nitrate_uptake_kg = subcanopy_volume_m3 * self.data["dissolved_nitrate"]
        phosphorus_uptake_kg = subcanopy_volume_m3 * self.data["dissolved_phosphorus"]

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
        # ratios
        seedbank_carbon_fraction = (
            subcanopy_npp * self.model_constants.subcanopy_reproductive_allocation
        ) / self.vegetation_biomass.carbon_mass

        seedbank_allocation = self.vegetation_biomass.remove_mass_fraction(
            mass_fraction=seedbank_carbon_fraction
        )

        # Extract seedbank provisioning using excess nutrients in vegetative biomass
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

        # Overwrite data in DataArrays with new numpy values.
        biomasses: dict[str, SubcanopyBiomass] = {
            "subcanopy_vegetation": self.seedbank_biomass,
            "subcanopy_seedbank": self.seedbank_biomass,
            "subcanopy_litter": vegetation_turnover,
            "seedbank_litter": seedbank_turnover,
        }

        for var, biomass in biomasses.items():
            self.data[f"{var}_biomass"].data = biomass.carbon_mass

            for elem in self.elements:
                self.data[f"{var}_c_{elem}_ratio"].data = biomass.c_x_ratio(elem)

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

        # MOVE INTO PLANTS MODEL
        #        self.ground_incident_light_fraction = (
        #            self.below_canopy_light_fraction * subcanopy_light_transmission
        #        )

        # Store those values
        self.data["leaf_area_index"][self.layer_index] = self.lai
        self.data["layer_fapar"][self.layer_index] = self.fapar
