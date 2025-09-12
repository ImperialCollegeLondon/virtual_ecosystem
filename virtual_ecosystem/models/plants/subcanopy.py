"""The subcanopy module provides blah blah blah

This is :class:`SubcanopyStoichiometry` is defined independently of the
:mod:`virtual_ecosystem.models.plants.stochiometry` module, as that class explicitly
handles communities of cohorts with multiple tissue types. The subcanopy has much
simpler structure with two stoichiometric masses per grid cell and so the dynamics are
more easily handled by a separate implementation.


"""  # noqa: D415

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst
from pyrealm.pmodel import PModel

from virtual_ecosystem.core.core_components import ModelTiming
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.plants.constants import PlantsConsts


class SubcanopyStoichiometry:
    """A stochiometry class for Subcanopy vegetation.

    The class tracks the carbon, nitrogen and phosphorous masses across an array of grid
    cells and provides properties to report the CN and CP ratios. It also provides
    methods to add and remove masses from the class and to remove excess nutrients above
    ideal ratios.
    """

    def __init__(
        self,
        carbon_mass: NDArray[np.floating],
        nitrogen_mass: NDArray[np.floating],
        phosphorous_mass: NDArray[np.floating],
        ideal_cn_ratio: float,
        ideal_cp_ratio: float,
    ) -> None:
        # Store Init arguments
        self.carbon_mass: NDArray[np.floating] = carbon_mass
        self.nitrogen_mass: NDArray[np.floating] = nitrogen_mass
        self.phosphorous_mass: NDArray[np.floating] = phosphorous_mass
        self.ideal_cn_ratio: float = ideal_cn_ratio
        self.ideal_cp_ratio: float = ideal_cp_ratio

    @property
    def c_n_ratio(self) -> NDArray[np.floating]:
        """Return the current CN ratio for the biomass."""
        return self.carbon_mass / self.nitrogen_mass

    @property
    def c_p_ratio(self) -> NDArray[np.floating]:
        """Return the current CP ratio for the biomass."""
        return self.carbon_mass / self.phosphorous_mass

    def remove_mass_fraction(self, mass_fraction: float) -> SubcanopyStoichiometry:
        """Remove a proportion of the biomass.

        This function returns a new SubcanopyStoichiometry object containing the
        requested fraction of the carbon biomass. The removed carbon biomass is removed
        from the parent instance. The nitrogen and phosphorous masses are split using
        the same fraction to maintain the same CN and CP ratios.

        Args:
            mass_fraction: The proportion of mass to remove from the instance.
        """

        carbon_out = self.carbon_mass * mass_fraction
        nitrogen_out = self.nitrogen_mass * mass_fraction
        phosphorous_out = self.phosphorous_mass * mass_fraction

        self.carbon_mass -= carbon_out
        self.nitrogen_mass -= nitrogen_out
        self.phosphorous_mass -= phosphorous_out

        return SubcanopyStoichiometry(
            carbon_mass=carbon_out,
            nitrogen_mass=nitrogen_out,
            phosphorous_mass=phosphorous_out,
            ideal_cn_ratio=self.ideal_cn_ratio,
            ideal_cp_ratio=self.ideal_cp_ratio,
        )

    def add_mass(self, source: SubcanopyStoichiometry):
        """Add biomass to a SubcanopyStoichiometry instance.

        The method adds the carbon, nitrogen and phosphorous biomasses from a source
        instance to the calling instance.

        Args:
            source: The source SubcanopyStoichiometry instance.
        """
        self.carbon_mass += source.carbon_mass
        self.nitrogen_mass += source.nitrogen_mass
        self.phosphorous_mass += source.phosphorous_mass

    def get_excess_nutrients(self) -> SubcanopyStoichiometry:
        """Extract excess nutrients.

        This method calculates the excess nitrogen and phosphorous biomass in a
        SubcanopyStoichiometry instance, given the provided ideal ratios. The method
        returns a SubcanopyStoichiometry instance containing excess nutrient masses.
        The carbon biomass in the returned instance will always be zero and nitrogen and
        phosphorous biomasses will also be zero where the source biomass in a cell is at
        or below the ideal ratio.
        """
        spare_nitrogen_mass = np.maximum(
            self.nitrogen_mass - (self.carbon_mass / self.ideal_cn_ratio), 0
        )
        spare_phosphorous_mass = np.maximum(
            self.phosphorous_mass - (self.carbon_mass / self.ideal_cp_ratio), 0
        )

        self.nitrogen_mass -= spare_nitrogen_mass
        self.phosphorous_mass -= spare_phosphorous_mass

        return SubcanopyStoichiometry(
            carbon_mass=np.zeros_like(self.carbon_mass),
            nitrogen_mass=spare_nitrogen_mass,
            phosphorous_mass=spare_phosphorous_mass,
            ideal_cn_ratio=self.ideal_cn_ratio,
            ideal_cp_ratio=self.ideal_cp_ratio,
        )


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

        # Stochiometry of vegetation and seedbank
        # TODO: currently initialising assuming ideal ratios but could load
        #       nutrient masses from init data.
        veg_mass = data["subcanopy_vegetation_biomass"].to_numpy()
        self.vegetation_biomass: SubcanopyStoichiometry = SubcanopyStoichiometry(
            carbon_mass=veg_mass,
            nitrogen_mass=veg_mass / model_constants.subcanopy_vegetation_cn_ratio,
            phosphorous_mass=veg_mass / model_constants.subcanopy_vegetation_cp_ratio,
            ideal_cn_ratio=model_constants.subcanopy_vegetation_cn_ratio,
            ideal_cp_ratio=model_constants.subcanopy_vegetation_cp_ratio,
        )

        seed_mass = data["subcanopy_seedbank_biomass"].to_numpy()
        self.seedbank_biomass: SubcanopyStoichiometry = SubcanopyStoichiometry(
            carbon_mass=seed_mass,
            nitrogen_mass=seed_mass / model_constants.subcanopy_seedbank_cn_ratio,
            phosphorous_mass=seed_mass / model_constants.subcanopy_seedbank_cp_ratio,
            ideal_cn_ratio=model_constants.subcanopy_seedbank_cn_ratio,
            ideal_cp_ratio=model_constants.subcanopy_seedbank_cp_ratio,
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
        self.vegetation_biomass.add_mass(
            SubcanopyStoichiometry(
                carbon_mass=subcanopy_npp,
                nitrogen_mass=ammonium_uptake_kg + nitrate_uptake_kg,
                phosphorous_mass=phosphorus_uptake_kg,
                ideal_cn_ratio=self.vegetation_biomass.ideal_cn_ratio,
                ideal_cp_ratio=self.vegetation_biomass.ideal_cp_ratio,
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
        biomasses: dict[str, SubcanopyStoichiometry] = {
            "subcanopy_vegetation": self.seedbank_biomass,
            "subcanopy_seedbank": self.seedbank_biomass,
            "subcanopy_litter": vegetation_turnover,
            "seedbank_litter": seedbank_turnover,
        }

        for var, biomass in biomasses.items():
            self.data[f"{var}_biomass"].data = biomass.carbon_mass
            self.data[f"{var}_c_n_ratio"].data = biomass.c_n_ratio
            self.data[f"{var}_c_p_ratio"].data = biomass.c_p_ratio

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
