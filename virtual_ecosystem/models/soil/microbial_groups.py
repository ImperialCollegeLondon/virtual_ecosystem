"""The ``models.soil.microbial_groups`` module contains the classes needed to define
the different microbial functional groups used in the soil model.
"""  # noqa: D205

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.soil.model_config import (
    REQUIRED_ENZYMES,
    SoilConfiguration,
    SoilEnzymeClass,
    SoilMicrobialGroup,
)


@dataclass(frozen=True)
class MicrobialGroupConstants:
    """Container for the set of constants associated with a microbial functional group.

    This sets out the constants which must be defined for each microbial functional
    group.
    """

    name: str
    """The name of the microbial group functional type."""

    taxonomic_group: str
    """The high level taxonomic group that the microbial group belongs to."""

    max_uptake_rate_labile_C: float
    """Maximum rate at the reference temperature of labile carbon uptake [day^-1]."""

    activation_energy_uptake_rate: float
    """Activation energy for nutrient uptake [J Kelvin^-1]."""

    half_sat_labile_C_uptake: float
    """Half saturation constant for uptake of labile carbon (LMWC) [kg{C} m^-3]."""

    activation_energy_uptake_saturation: float
    """Activation energy for nutrient uptake saturation constants [J Kelvin^-1]."""

    max_uptake_rate_ammonium: float
    """Maximum possible rate for ammonium uptake [day^-1]."""

    half_sat_ammonium_uptake: float
    """Half saturation constant for uptake of ammonium [kg{N} m^-3]."""

    max_uptake_rate_nitrate: float
    """Maximum possible rate for nitrate uptake [day^-1]."""

    half_sat_nitrate_uptake: float
    """Half saturation constant for uptake of nitrate [kg{N} m^-3]."""

    max_uptake_rate_labile_p: float
    """Maximum possible rate for labile inorganic phosphorus uptake [day^-1]."""

    half_sat_labile_p_uptake: float
    """Half saturation constant for uptake of labile inorganic phosphorus [kg{P} m^-3].
    """

    turnover_rate: float
    """Microbial maintenance turnover rate at reference temperature [day^-1]."""

    activation_energy_turnover: float
    """Activation energy for microbial maintenance turnover rate [J Kelvin^-1]."""

    reference_temperature: float
    """The reference temperature that turnover and uptake rates were measured at
    [Celsius].
    """

    c_n_ratio: float
    """Ratio of carbon to nitrogen in biomass [unitless]."""

    c_p_ratio: float
    """Ratio of carbon to phosphorus in biomass [unitless]."""

    enzyme_production: dict[str, float]
    """Details of the enzymes produced by the microbial group.
    
    The keys are the substrates for which enzymes are produced, and the values are the
    allocation to enzyme production. This allocation is expressed as a fraction of the
    (gross) cellular biomass growth [unitless].
    """

    reproductive_allocation: float
    """Reproductive allocation as fraction of (gross) cellular biomass growth [unitless]
    
    Only fungi generate separate reproductive bodies, so this value **must** be set to
    zero for bacterial functional groups. Providing a non-zero value for a bacterial
    functional group will prevent the soil model from configuring.
    """

    symbiote_nitrogen_uptake_fraction: float
    """Fraction of nitrogen uptake that is supplied to symbiotic (plant) partners.    
    [unitless]. 
    
    This should only have a non-zero value for mycorrhizal fungi.
    """

    symbiote_phosphorus_uptake_fraction: float
    """Fraction of phosphorus uptake that is supplied to symbiotic (plant) partners.    
    [unitless]. 
    
    This should only have a non-zero value for mycorrhizal fungi.
    """

    synthesis_nutrient_ratios: dict[str, float]
    """Average carbon to nutrient ratios for the total synthesised biomass [unitless].
    
    Microbes have to synthesis both cellular biomass and extracellular enzymes. We
    assume that this occurs in fixed unvarying proportion. This attribute stores the
    carbon nutrient (nitrogen, phosphorus) ratios for the total synthesised biomass.
    """

    @classmethod
    def build_microbial_group(
        cls,
        group_config: SoilMicrobialGroup,
        enzyme_classes: dict[str, SoilEnzymeClass],
        core_constants: CoreConstants,
    ):
        """Class method to build the microbial group including enzyme information.

        Args:
            group_config: A SoilMicrobialGroup instance.
            enzyme_classes: Details of the enzyme classes used by the soil model.
            core_constants: Set of constants shared across the Virtual Ecosystem models.
        """

        return cls(
            **group_config.model_dump(),
            synthesis_nutrient_ratios=calculate_new_biomass_average_nutrient_ratios(
                taxonomic_group=group_config.taxonomic_group,
                c_n_ratio=group_config.c_n_ratio,
                c_p_ratio=group_config.c_p_ratio,
                enzyme_production=group_config.enzyme_production,
                reproductive_allocation=group_config.reproductive_allocation,
                enzyme_classes=enzyme_classes,
            ),
        )

    def find_enzyme_substrates(self) -> list[str]:
        """Substrates that the microbial group produces enzymes for."""

        return [
            substrate
            for substrate, production in self.enzyme_production.items()
            if production > 0.0
        ]


def calculate_new_biomass_average_nutrient_ratios(
    taxonomic_group: str,
    c_n_ratio: float,
    c_p_ratio: float,
    enzyme_production: dict[str, float],
    reproductive_allocation: float,
    enzyme_classes: dict[str, SoilEnzymeClass],
) -> dict[str, float]:
    """Calculate average carbon nutrient ratios of the newly synthesised biomass.

    Microbes have to synthesise cellular biomass as well as extracellular enzymes, and
    fungi also allocate to reproductive fruiting bodies. This method calculates average
    nutrient ratios of this total biomass synthesis using the relative production
    allocation to each enzyme class, cellular growth and (for fungi) reproductive
    allocation. Carbon nutrient ratios have units of carbon per nutrient and so cannot
    be simply averaged across the different biomass allocations, which are all expressed
    in carbon terms. Instead, they must first be inversed to convert to nutrient per
    carbon units, and then the average of these inverses can be found.

    Args:
        taxonomic_group: Taxonomic group that the microbe belongs to.
        c_n_ratio: Ratio of carbon to nitrogen for the microbial group's cellular
            biomass.
        c_p_ratio: Ratio of carbon to nitrogen for the microbial group's cellular
            biomass.
        enzyme_production: Details of the enzymes produced by the microbial group, i.e.
            which substrates are enzymes produced for, and how much (relative to
            cellular synthesis)
        reproductive_allocation: Allocation of new biomass synthesis to reproductive
            structures (relative to cellular synthesis).
        enzyme_classes: Details of the enzyme classes used by the soil model.
    """

    enzyme_c_n_inverse = sum(
        allocation / enzyme_classes[f"{taxonomic_group}_{substrate}"].c_n_ratio
        for substrate, allocation in enzyme_production.items()
    )

    enzyme_c_p_inverse = sum(
        allocation / enzyme_classes[f"{taxonomic_group}_{substrate}"].c_p_ratio
        for substrate, allocation in enzyme_production.items()
    )

    total_carbon_gain = 1 + sum(enzyme_production.values()) + reproductive_allocation

    return {
        "nitrogen": total_carbon_gain
        / (((1 + reproductive_allocation) / c_n_ratio) + enzyme_c_n_inverse),
        "phosphorus": total_carbon_gain
        / (((1 + reproductive_allocation) / c_p_ratio) + enzyme_c_p_inverse),
    }


def make_full_set_of_microbial_groups(
    config: SoilConfiguration,
    enzyme_classes: dict[str, SoilEnzymeClass],
    core_constants: CoreConstants,
) -> dict[str, MicrobialGroupConstants]:
    """Make the full set of functional groups used in the soil model.

    Args:
        config: A soil model configuration instance.
        enzyme_classes: Details of the enzyme classes used by the soil model.
        core_constants: Set of constants shared across the Virtual Ecosystem models.

    Returns:
        A dictionary containing each required functional group used in the soil model.
    """

    return {
        group.name: MicrobialGroupConstants.build_microbial_group(
            group_config=group,
            core_constants=core_constants,
            enzyme_classes=enzyme_classes,
        )
        for group in config.microbial_group_definition
    }


def make_full_set_of_enzyme_classes(path_to_csv: str) -> dict[str, SoilEnzymeClass]:
    """Make the full set of enzyme classes used in the soil model.

    Args:
        path_to_csv: Path to a csv file containing definitions of the parametrisation of
            the enzymes used in the soil model.

    Raises:
        ConfigurationError: If the provided path doesn't point to a csv file.
        InitialisationError: If a required enzyme parameter isn't included in the csv
            file, if a required enzyme class isn't defined, or if enzymes classes cannot
            be created using the values provided in the csv file.

    Returns:
        A dictionary containing each required enzyme class used in the soil model.
    """

    # First check path and raise an error if it doesn't point to a csv file
    enzyme_definition_path = Path(path_to_csv)

    if (
        not enzyme_definition_path.is_file()
        or not enzyme_definition_path.suffix.lower() == ".csv"
    ):
        error_to_raise = ConfigurationError(
            "The file path provided to the enzyme class definition file doesn't point "
            f"to a csv file: {enzyme_definition_path}"
        )
        LOGGER.error(error_to_raise)
        raise error_to_raise

    # Then check that the csv has the expected headers (and if not error)
    required_headers = [f for f in SoilEnzymeClass.model_fields]

    enzyme_definitions = pd.read_csv(enzyme_definition_path)
    actual_headers = enzyme_definitions.columns.tolist()

    missing = set(required_headers) - set(actual_headers)
    surplus = set(actual_headers) - set(required_headers)

    if missing:
        to_raise = InitialisationError(
            "The following expected headers are missing from the enzyme class "
            f"definition file: {missing}"
        )
        LOGGER.error(to_raise)
        raise to_raise

    # Surplus headers aren't a big enough issue to warrant killing the simulation, but
    # are still worth emitting a warning for
    if surplus:
        msg = (
            "The following additional headers are provided in the enzyme class "
            f"definition file, and were ignored: {surplus}"
        )
        LOGGER.warning(msg)

    # Check that all expected enzymes are defined in the csv (otherwise log an error)
    defined_enzymes = pd.MultiIndex.from_frame(
        enzyme_definitions[["source", "substrate"]].drop_duplicates()
    )
    missing_enzymes = REQUIRED_ENZYMES.difference(defined_enzymes)
    # Also should check for unexpected or duplicate enzymes
    unexpected_enzymes = set(defined_enzymes.difference(REQUIRED_ENZYMES))
    duplicated_enzymes = enzyme_definitions.duplicated(subset=["source", "substrate"])

    if missing_enzymes:
        to_raise = InitialisationError(
            "The following required enzymes are not defined in the enzyme class "
            f"definition file: {missing_enzymes}"
        )
        LOGGER.error(to_raise)
        raise to_raise

    if unexpected_enzymes:
        to_raise = InitialisationError(
            "The following enzyme class are provided in the definition file but are "
            f"not expected by the simulation: {unexpected_enzymes}"
        )
        LOGGER.error(to_raise)
        raise to_raise

    if any(duplicated_enzymes):
        to_raise = InitialisationError(
            "Enzyme definition file contains duplicate copies of enzymes!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    enzyme_classes = {}
    failed_rows = []

    for idx, row in enzyme_definitions.iterrows():
        try:
            data = row[required_headers].to_dict()

            enzyme = SoilEnzymeClass(**data)
            enzyme_name = f"{row['source']}_{row['substrate']}"
            enzyme_classes[enzyme_name] = enzyme

        except (ValueError, TypeError):
            failed_rows.append(idx)

    if failed_rows:
        to_raise = InitialisationError(
            "The following rows in the enzyme class definition file contained bad data:"
            f" {failed_rows}"
        )
        LOGGER.error(to_raise)
        raise to_raise

    return enzyme_classes


@dataclass
class CarbonSupply:
    """Rate of carbon supply to each of the plant symbiotic microbial groups."""

    nitrogen_fixers: NDArray[np.floating]
    """Carbon supply to the nitrogen fixing bacteria [kg{C} m^-3 day^-1]."""

    ectomycorrhiza: NDArray[np.floating]
    """Carbon supply to ectomycorrhizal fungi [kg{C} m^-3 day^-1]."""

    arbuscular_mycorrhiza: NDArray[np.floating]
    """Carbon supply to arbuscular mycorrhizal fungi [kg{C} m^-3 day^-1]."""


def calculate_symbiotic_carbon_supply(
    total_plant_supply: NDArray[np.floating],
    nitrogen_fixer_fraction: float,
    ectomycorrhiza_fraction: float,
) -> CarbonSupply:
    """Calculate supply of carbon from plants to each microbial symbiotic partner.

    This function splits the total carbon supply from the plants between the different
    symbiotic microbial groups based on (configurable) constant fractions.

    Args:
        total_plant_supply: Total supply of carbon from the plant to symbiotic microbial
            partners [kg{C} m^-3 day^-1]
        nitrogen_fixer_fraction: Fraction of carbon supplied by plants to symbiotes that
            goes to nitrogen fixers [unitless]
        ectomycorrhiza_fraction: Fraction of plant carbon supply to mycorrhizal fungi
            that goes to ectomycorrhiza [unitless]

    Returns:
        The carbon supply to each symbiotic microbial partner [kg{C} m^-3 day^-1]
    """

    n_fixer_supply = total_plant_supply * nitrogen_fixer_fraction

    mycorrhiza_supply = total_plant_supply * (1 - nitrogen_fixer_fraction)
    ectomycorrhiza_supply = mycorrhiza_supply * ectomycorrhiza_fraction
    arbuscular_mycorrhiza_supply = mycorrhiza_supply * (1 - ectomycorrhiza_fraction)

    return CarbonSupply(
        nitrogen_fixers=n_fixer_supply,
        ectomycorrhiza=ectomycorrhiza_supply,
        arbuscular_mycorrhiza=arbuscular_mycorrhiza_supply,
    )
