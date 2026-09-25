"""The subcanopy module provides a representation of subcanopy biomass pools:

* Subcanopy vegetation biomass,
* Subcanopy seedbank biomass,
* Subcanopy vegetation litter biomass,
* Subcanopy seedbank litter biomass,

All these pools use a stoichiometric representation of biomasses as n_cells by
n_elements array. This system is similar to the
:mod:`virtual_ecosystem.models.plants.biomasses` module, but that class explicitly
handles communities of cohorts with multiple tissue types. The subcanopy has much
simpler representation with only four simple pools and so the dynamics are more easily
handled by a separate implementation.

The module implements the following classes:

* The :class:`SubcanopyBiomass` class tracks the elemental masses within a pool and
  provides methods to add and remove biomasses and extract surplus nutrients.
* The :class:`Subcanopy` then maintains subcanopy biomass pools for the vegetation and
  seedbank and provides methods to update the light gathering and ecological dynamics of
  the subcanopy pools at each update step.
"""  # noqa: D415

from __future__ import annotations

from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst
from pyrealm.core.water import convert_water_moles_to_mm
from pyrealm.pmodel import PModel
from xarray import DataArray

from virtual_ecosystem.core.core_components import ModelTiming
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.plants.model_config import PlantsConstants


class SubcanopyBiomass:
    """Stoichiometry representation of tissue biomass pools for the subcanopy.

    This class holds the current elemental masses for a subcanopy tissue pool.

    * The elemental biomasses are held as a numpy array with a column for each
      element and a row for each cell id. Carbon masses are always in the first column,
      followed by the nutrient elements given in the the ``elements`` class attribute.
      The initial biomasses are set from provided data.

    * The ideal ratios are held as numpy arrays, with the same shape as the biomasses
      and are expressed as C/x ratios. The first column of these arrays should always be
      one and therefore C/C and should therefore always be set as one.

    The class provides methods to add and remove biomasses and to extract excess
    nutrients from tissues.

    Args:
        initial_masses: The initial set of elemental biomasses.
        ideal_ratios: The ideal stochiometric ratios for the tissue.
        var_name: The variable name used for the tissue in the data object.
    """

    elements: ClassVar[tuple[str, ...]] = ("N", "P")
    """A tuple giving the nutrient elements included in the biomasses."""

    def __init__(
        self,
        initial_masses: NDArray[np.floating],
        ideal_ratios: NDArray[np.floating],
        var_name: str,
    ):

        # TODO - check shapes needs n_cells.

        # Handle initial mass NaN setup
        nan_masses = np.isnan(initial_masses)

        # Carbon values all filled
        if np.any(nan_masses[:, 0]):
            raise ValueError("NaN values in carbon masses in subcanopy tissue.")

        # Are all nutrient values missing
        nutrients_all_nan = np.all(nan_masses[:, 1:])

        # Catch partial data case
        if np.any(nan_masses) and not nutrients_all_nan:
            raise ValueError(
                f"Incomplete elemental nutrient masses in {var_name}: "
                "either provide all values or none to use ideal ratios. "
            )

        # If no nutrient data provided, then fill in using ideal ratios
        if nutrients_all_nan:
            initial_masses = initial_masses[:, [0]] / ideal_ratios

        self.elemental_masses: NDArray[np.floating] = initial_masses
        """An 2D array of subcanopy tissue elemental masses across cells."""

        self.ideal_ratios: NDArray[np.floating] = ideal_ratios
        """Ideal elemental ratios for the subcanopy tissue."""

        self.var_name: str = var_name
        """Variable name used for these masses in the data object."""

    def remove_mass_fraction(
        self, mass_fraction: float | NDArray[np.floating]
    ) -> SubcanopyBiomass:
        """Remove a proportion of the biomass.

        This function removes a requested fraction of the biomass from a parent instance
        and returns a new SubcanopyBiomass object containing that biomass. The elemental
        ratios are maintained.

        Args:
            mass_fraction: The proportion of mass to remove from each cell in the
                instancem, either as a single value or an array of per cells values
        """

        # Rotate per cell array into a column vector
        if isinstance(mass_fraction, np.ndarray):
            mass_fraction = mass_fraction[:, None]

        # Extract biomasses
        biomass_loss = self.elemental_masses * mass_fraction
        self.elemental_masses -= biomass_loss

        # Return extracted biomasses
        return SubcanopyBiomass(
            initial_masses=biomass_loss,
            ideal_ratios=self.ideal_ratios,
            var_name=self.var_name,
        )

    def add_mass(self, source: SubcanopyBiomass):
        """Add biomass to a SubcanopyBiomass instance.

        The method adds carbon and nutrient biomasses to the calling instance.

        Args:
            source: The source biomass instance.
        """

        self.elemental_masses += source.elemental_masses

    def get_excess_nutrients(self) -> SubcanopyBiomass:
        """Extract excess nutrients.

        This method removes excess nutrient element biomass from a SubcanopyBiomass
        instance, given the provided ideal ratios. The method returns another
        SubcanopyBiomass instance containing zero carbon mass but including excess
        nutrient masses: these will also be zero where the source biomass in a cell is
        at or below the ideal ratio.
        """

        excess = np.clip(
            a=self.elemental_masses
            - (self.elemental_masses[:, [0]] / self.ideal_ratios),
            a_min=0,
            a_max=None,
        )
        self.elemental_masses -= excess
        return SubcanopyBiomass(
            initial_masses=excess,
            ideal_ratios=self.ideal_ratios,
            var_name=self.var_name,
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
        pyrealm_core_constants: The PModel core constants for the simulation.
        model_constants: The PlantModel constants for the simulation
        layer_index: The layer index of the surface layer in the vertical layer axis.
        model_timing: The core ModelTiming instance for the simulation.
        data_object_template: A template for creating CNP element arrays.
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
        data_object_template: DataArray,
    ) -> None:
        # Init attributes
        self.data: Data = data
        """The Data instance for a simulation."""
        self.pyrealm_core_constants: CoreConst = pyrealm_core_constants
        """The pyrealm core constants set used."""
        self.model_constants: PlantsConstants = model_constants
        """The plants model constants set used."""
        self.model_timing: ModelTiming = model_timing
        """The model timing instance of the simulation."""
        self.layer_index: int = layer_index
        """The layer index of the subcanopy."""
        self.data_object_template: DataArray = data_object_template
        """A template for arrays of stochiometric element masses across cell id."""

        # Stochiometry of vegetation and seedbank
        self.subcanopy_vegetation_cnp: SubcanopyBiomass = SubcanopyBiomass(
            initial_masses=data["subcanopy_vegetation_cnp"].to_numpy(),
            ideal_ratios=np.array(
                [
                    1,
                    model_constants.subcanopy_vegetation_c_n_ratio,
                    model_constants.subcanopy_vegetation_c_p_ratio,
                ]
            ),
            var_name="subcanopy_vegetation_cnp",
        )
        """The stoichiometric vegetative biomasses in the subcanopy [kg m-2]."""

        self.subcanopy_seedbank_cnp: SubcanopyBiomass = SubcanopyBiomass(
            initial_masses=data["subcanopy_seedbank_cnp"].to_numpy(),
            ideal_ratios=np.array(
                [
                    1,
                    model_constants.subcanopy_seedbank_c_n_ratio,
                    model_constants.subcanopy_seedbank_c_p_ratio,
                ]
            ),
            var_name="subcanopy_seedbank_cnp",
        )
        """The stoichiometric reproductive biomasses in the subcanopy [kg m-2]."""

        # Initialise the litter pools - the ideal ratios are meaningless here.
        empty_litter = np.zeros_like(self.subcanopy_vegetation_cnp.elemental_masses)
        self.subcanopy_seedbank_litter_cnp: SubcanopyBiomass = SubcanopyBiomass(
            initial_masses=empty_litter.copy(),
            ideal_ratios=np.array([1, 1, 1]),
            var_name="subcanopy_seedbank_litter_cnp",
        )
        """Stoichiometric additions to the subcanopy seedbank litter pool [kg m-2]"""

        self.subcanopy_vegetation_litter_cnp: SubcanopyBiomass = SubcanopyBiomass(
            initial_masses=empty_litter.copy(),
            ideal_ratios=np.array([1, 1, 1]),
            var_name="subcanopy_vegetation_litter_cnp",
        )
        """Stoichiometric additions to the subcanopy vegetation litter pool [kg m-2]"""

        self.write_biomasses_pools_to_data()

        # Type other attributes not populated at __init__
        self.lai: NDArray[np.floating]
        """The leaf area index of the subcanopy."""
        self.light_transmission: NDArray[np.floating]
        """The light transmission of the subcanopy."""
        self.fapar: NDArray[np.floating]
        """The FAPAR of the subcanopy."""
        self.subcanopy_transpiration: NDArray[np.floating]
        """Total transpiration of the subcanopy for a model step."""
        self.subcanopy_gpp: NDArray[np.floating]
        """Total GPP of the subcanopy for a model step."""

    def write_biomasses_pools_to_data(self):
        """Exports the subcanopy biomass pools to the data object."""
        for biomass_pool in [
            "subcanopy_vegetation_cnp",
            "subcanopy_seedbank_cnp",
            "subcanopy_seedbank_litter_cnp",
            "subcanopy_vegetation_litter_cnp",
        ]:
            self.data[biomass_pool] = self.data_object_template.copy(
                data=getattr(self, biomass_pool).elemental_masses
            )

    def estimate_gpp(
        self,
        pmodel: PModel,
        swd: NDArray[np.floating],
    ) -> None:
        r"""Estimate the GPP and transpiration of the subcanopy.

        This method estimates the GPP and transpiration for the subcanopy using the
        current P Model conditions in the subcanopy layer. The GPP and transpiration may
        then be penalised by water limitation before calculating the subcanopy dynamics.
        """

        # Calculate the gross primary productivity since the last update.
        #    LUE                 1 layer          [gC mol-1]
        #    * canopy top SWD    1 layer          [µmol m-2 s-1]
        #    * subcanopy fapar   1 layer          [-]
        #    * DST to PPFD       scalar           [-]
        #    * time elapsed      scalar           [s]
        # Units:
        #    gC mol-1 * µmol m-2 s-1  * (-) * (-) * s = µg C m-2
        #
        # This calculation handles non-estimable LUE from the P Model by setting np.nan
        # values to zero.
        self.subcanopy_gpp = (
            np.nan_to_num(pmodel.lue[self.layer_index, :])
            * swd
            * self.fapar
            * self.model_constants.dsr_to_ppfd
            * self.model_timing.update_interval_seconds
        )

        # Calculate the transpiration associated with the GPP in moles
        subcanopy_transpiration_micromolar = (
            self.subcanopy_gpp / (self.pyrealm_core_constants.k_c_molmass * 1e6)
        ) * pmodel.iwue[self.layer_index, :]

        # Convert to mm using the local subcanopy environment
        self.subcanopy_transpiration = convert_water_moles_to_mm(
            water_moles=subcanopy_transpiration_micromolar * 1e-6,
            tc=pmodel.env.tc[self.layer_index, :],
            patm=pmodel.env.patm[self.layer_index, :],
            core_const=self.pyrealm_core_constants,
        )

        # Write transpiration data
        self.data["transpiration"][self.layer_index] = self.subcanopy_transpiration

    def calculate_dynamics(self) -> None:
        r"""Estimate the dynamics of subcanopy vegetation.

        This method models the biomass dynamics with the subcanopy vegetation and
        subcanopy seedbank pools during a model update.

        1. A fraction of the biomass in each pool is allocated to turnover, and passed
           into litter pools. The stoichiometric ratios of turnover biomass are
           identical to the pool biomasses.

        2. The estimated gross primary productivity (GPP) and transpiration (see
           :meth:`estimate_gpp`) are used to estimate growth and nutrient uptake. GPP is
           reduced by respiration and yield to give net primary productivity NPP, which
           is added as new carbon biomass to the subcanopy vegetation. The soil
           dissolved nitrate, ammonium and phosphorous concentrations are then used to
           calculate the nutrient uptake associated with the transpiration volume and
           these are added to the subcanopy vegetation pool.

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

        # Recreate new litter pools with turnover for this timestep
        self.subcanopy_vegetation_litter_cnp = (
            self.subcanopy_vegetation_cnp.remove_mass_fraction(
                self.model_constants.subcanopy_vegetation_turnover
                / self.model_timing.updates_per_year
            )
        )

        self.subcanopy_seedbank_litter_cnp = (
            self.subcanopy_seedbank_cnp.remove_mass_fraction(
                self.model_constants.subcanopy_seedbank_turnover
                / self.model_timing.updates_per_year
            )
        )

        # Calculate NPP, converting µg C m-2 to  kg C m-2
        # TODO - what is the fate of the (1- self.model_constants.subcanopy_yield). The
        #        assumption here is that it is lost to the atmosphere, but that is
        #        basically the same as respiration?
        subcanopy_npp = (
            self.model_constants.subcanopy_yield
            * (self.subcanopy_gpp * 1e-9)
            * (1 - self.model_constants.subcanopy_respiration_fraction)
        )

        # Transpiration and nutrient acquisition

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

        # Assimilate the gained masses into the vegetation first to update the
        # nutrient masses that are available for allocation to seedbank
        nutrient_uptake = np.hstack(
            [
                subcanopy_npp[:, None],
                (ammonium_uptake_kg + nitrate_uptake_kg)[:, None],
                phosphorus_uptake_kg[:, None],
            ]
        )

        self.subcanopy_vegetation_cnp.elemental_masses += nutrient_uptake

        # Extract the new carbon allocation for the seedbank using those new nutrient
        # ratios, catching cells with no vegetation biomass
        seedbank_carbon_fraction: NDArray[np.floating] = np.where(
            self.subcanopy_vegetation_cnp.elemental_masses[:, 0] > 0,
            (subcanopy_npp / self.subcanopy_vegetation_cnp.elemental_masses[:, 0])
            * self.model_constants.subcanopy_reproductive_allocation,
            0,
        )
        seedbank_allocation = self.subcanopy_vegetation_cnp.remove_mass_fraction(
            mass_fraction=seedbank_carbon_fraction
        )

        # Extract seedbank provisioning using excess nutrients in vegetative biomass
        seedbank_extra_nutrients = self.subcanopy_vegetation_cnp.get_excess_nutrients()

        # Get the new sprouted biomass from the seedbank during the time period
        sprouting_biomass = self.subcanopy_seedbank_cnp.remove_mass_fraction(
            self.model_constants.subcanopy_sprout_rate
            / self.model_timing.updates_per_year
        )

        # Remove the sprouting biomass yield losses from the total mass
        sprouting_yield_losses = sprouting_biomass.remove_mass_fraction(
            mass_fraction=1 - self.model_constants.subcanopy_sprout_yield
        )

        # Now allocate new biomasses to pools
        self.subcanopy_seedbank_cnp.add_mass(seedbank_allocation)
        self.subcanopy_seedbank_cnp.add_mass(seedbank_extra_nutrients)
        self.subcanopy_vegetation_cnp.add_mass(sprouting_biomass)
        self.subcanopy_seedbank_litter_cnp.add_mass(sprouting_yield_losses)

        # Write biomass pool and nutrient uptake data to
        self.write_biomasses_pools_to_data()

        coords = {"cell_id": self.data["cell_id"].data}
        for name, values in (
            ("subcanopy_ammonium_uptake", ammonium_uptake_kg),
            ("subcanopy_nitrate_uptake", nitrate_uptake_kg),
            ("subcanopy_phosphorus_uptake", phosphorus_uptake_kg),
        ):
            self.data[name] = DataArray(values, coords=coords)

    def set_light_capture(self, below_canopy_light_fraction: NDArray) -> None:
        r"""Calculate the leaf area index and absorption of subcanopy vegetation.

        The subcanopy vegetation is represented as a single pool of biomass with
        associated stoichiometric values but, when calculating light capture, the pool
        is divided into structural and leaf biomass components. The
        :attr:`virtual_ecosystem.models.plants.model_config.PlantsConstants.subcanopy_leaf_fraction`
        configuration setting defines the subcanopy leaf biomass (:math:`M_{SC}`, kg C
        m-2) as a fraction of the total subcanopy biomass pool.
        
        The model consstants also define subcanopy values for the light extinction
        coefficient (:math:`k`) and specific leaf area (:math:`\sigma`, m2 kg-1 C).
        These can be used to calculate the leaf area index (:math:`L`) and hence the
        absorption fraction (:math:`f_{a}`) of  the subcanopy leaf biomass via the
        Beer-Lambert law: 

        .. math ::
            :nowrap:

            \[
                \begin{align*}
                    L &= M_{SC} \sigma \\
                    f_a = e^{-kL}
                \end{align*}
            \]

        .. WARNING::

            The subcanopy growth dynamics can lead to very high leaf area index in the
            subcanopy, which crash the calculation of abiotic balances in the
            model. Currently the subcanopy LAI is explicitly capped, using the setting
            :attr:`virtual_ecosystem.models.plants.model_config.PlantsConstants.subcanopy_maximum_leaf_area_index`
            to artificially prevent model crashes. This is a temporary feature and
            should be replaced by better biological and environmental control of
            subcanopy growth.
        """

        # Calculate the leaf area index - values are already in kg m-2 so no need to
        # account for the area occupied by the biomass. This code accounts for the
        # structural fraction of the subcanopy and caps the resulting LAI.
        self.lai = np.clip(
            self.subcanopy_vegetation_cnp.elemental_masses[:, 0]  # carbon mass
            * self.model_constants.subcanopy_specific_leaf_area
            * self.model_constants.subcanopy_leaf_fraction,
            a_min=0,
            a_max=self.model_constants.subcanopy_maximum_leaf_area_index,
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
