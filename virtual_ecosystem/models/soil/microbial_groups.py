"""The ``models.soil.microbial_groups`` module contains the classes needed to define
the different microbial functional groups used in the soil model.
"""  # noqa: D205

from __future__ import annotations

from dataclasses import InitVar, dataclass
from functools import cached_property
from itertools import product
from pathlib import Path
from typing import Literal, get_args

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pydantic import ConfigDict, Field, ValidationError, computed_field, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from virtual_ecosystem.core.configuration import Configuration

REQUIRED_MICROBIAL_GROUPS = Literal[
    "saprotrophic_fungi",
    "ectomycorrhiza",
    "arbuscular_mycorrhiza",
    "bacteria",
]
"""Required taxonomic groups in the soil model"""

HIGHER_TAXONOMIC_GROUPS = Literal["fungi", "bacteria"]
"""Permitted higher taxonomic group names in the soil model."""

SUBSTRATES = Literal["pom", "maom"]
"""Permitted substrate types in the soil model"""

REQUIRED_ENZYMES: set[tuple[HIGHER_TAXONOMIC_GROUPS, SUBSTRATES]] = set(
    product(get_args(HIGHER_TAXONOMIC_GROUPS), get_args(SUBSTRATES))
)
"""Required enzyme classes as all pairs of higher taxon source and substrate."""


class SoilEnzyme(Configuration):
    """Container for the set of constants associated with a soil enzyme class.

    This sets out the constants which must be defined for each soil enzyme class.
    """

    source: HIGHER_TAXONOMIC_GROUPS
    """The higher microbial group which produces the enzyme."""
    substrate: SUBSTRATES
    """The substrate which the enzyme acts upon."""
    maximum_rate: float
    """The maximum rate of the enzyme at the reference temperature [day-1]."""
    half_saturation_constant: float
    """The half saturation constant for the enzyme at the reference temperature. Units
    of [kg{C} m-3]."""
    activation_energy_rate: float
    """Activation energy for enzyme rate with temperature [J mol-1]."""
    activation_energy_saturation: float
    """Activation energy for enzyme saturation with temperature [J mol-1]."""
    # TODO - This should change to Kelvin when we change the default units to Kelvin
    reference_temperature: float
    """The temperature that enzyme rate and saturation were measured at [Celsius]."""
    turnover_rate: float
    """The turnover rate of the enzyme [day-1]."""
    c_n_ratio: float
    """Ratio of carbon to nitrogen for the enzyme [unitless]."""
    c_p_ratio: float
    """Ratio of carbon to phosphorus for the enzyme [unitless]."""


def load_enzymes(path: Path) -> dict[str, SoilEnzyme]:
    """Load and validate a soil enzyme CSV file.

    Args:
        path: Path to csv file containing parametrisation for the required enzymes.

    Raises:
        ValueError: If the path doesn't point to a readable csv file, or if that csv
            file is missing headers, contains surplus headers, is missing required
            enzymes, contains duplicate enzymes or contains enzymes that aren't expected
            by the simulation.

    Returns:
        The full set of enzymes required by the soil model.
    """

    # Try and load the data
    try:
        data = pd.read_csv(path)
    except (FileNotFoundError, IsADirectoryError):
        raise ValueError(f"Enzyme CSV path not found or a directory: {path}")
    except pd.errors.ParserError as excep:
        raise ValueError(f"Could not parse enzyme data from: {path}: {excep!s}")

    # Validate the data
    try:
        # Validate the CSV records
        enzymes = [
            SoilEnzyme.model_validate(rec) for rec in data.to_dict(orient="records")
        ]
    except ValidationError as excep:
        raise ValueError(f"Invalid data in enzyme CSV file: {excep!s}")

    # Check the set of enzymes
    provided_enzymes = [(e.source, e.substrate) for e in enzymes]
    set_provided_enzymes = set(provided_enzymes)

    if len(set_provided_enzymes) != len(provided_enzymes):
        raise ValueError(
            "Duplicated enzyme source/substrate combinations in enzyme data"
        )

    if not set_provided_enzymes == REQUIRED_ENZYMES:
        raise ValueError(
            f"The source/substrate pairs provided in enzyme class definitions "
            f"({provided_enzymes!r}) do not match the required set of pairs "
            f"({REQUIRED_ENZYMES!r})"
        )

    # Package into a dict and return
    return {f"{r.source}_{r.substrate}": r for r in enzymes}


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class SoilMicrobe:
    """Microbial functional group definitions."""

    # No docstring for this attribute as it disappears after the class is initialised
    enzyme_classes: InitVar[dict[str, SoilEnzyme]]

    name: REQUIRED_MICROBIAL_GROUPS
    """The name of the microbial group functional type."""
    taxonomic_group: HIGHER_TAXONOMIC_GROUPS
    """The high level taxonomic group that the microbial group belongs to."""
    max_uptake_rate_labile_C: float
    """Maximum rate at the reference temperature of labile carbon uptake [day-1]."""
    activation_energy_uptake_rate: float
    """Activation energy for nutrient uptake [J mol-1]."""
    half_sat_labile_C_uptake: float
    """Half saturation constant for uptake of labile carbon (LMWC) [kg{C} m-3]."""
    activation_energy_uptake_saturation: float
    """Activation energy for nutrient uptake saturation constants [J mol-1]."""
    max_uptake_rate_ammonium: float
    """Maximum possible rate for ammonium uptake [day-1]."""
    half_sat_ammonium_uptake: float
    """Half saturation constant for uptake of ammonium [kg{N} m-3]."""
    max_uptake_rate_nitrate: float
    """Maximum possible rate for nitrate uptake [day-1]."""
    half_sat_nitrate_uptake: float
    """Half saturation constant for uptake of nitrate [kg{N} m-3]."""
    max_uptake_rate_labile_p: float
    """Maximum possible rate for labile inorganic phosphorus uptake [day-1]."""
    half_sat_labile_p_uptake: float
    """Half saturation constant for uptake of labile inorganic phosphorus [kg{P} m-3].
    """
    turnover_rate: float
    """Microbial maintenance turnover rate at reference temperature [day-1]."""
    activation_energy_turnover: float
    """Activation energy for microbial maintenance turnover rate [J mol-1]."""
    reference_temperature: float
    """The temperature that turnover and uptake rates were measured at [Celsius]."""
    c_n_ratio: float
    """Ratio of carbon to nitrogen in biomass [unitless]."""
    c_p_ratio: float
    """Ratio of carbon to phosphorus in biomass [unitless]."""
    enzyme_production_pom: float = Field(ge=0.0, le=1.0)
    """Fraction of (gross) cellular biomass production allocated to production of
    enzymes that break down :term:`POM` [unitless]."""
    enzyme_production_maom: float = Field(ge=0.0, le=1.0)
    """Fraction of (gross) cellular biomass production allocated to production of
    enzymes that break down :term:`MAOM` [unitless]."""
    reproductive_allocation: float = Field(ge=0.0, le=1.0)
    """Reproductive allocation as fraction of (gross) cellular biomass growth [unitless]
    Only fungi generate separate reproductive bodies, so this value **must** be set to
    zero for bacterial functional groups. Providing a non-zero value for a bacterial
    functional group will prevent the soil model from configuring.
    """
    symbiote_nitrogen_uptake_fraction: float = Field(ge=0.0, le=1.0)
    """Fraction of nitrogen uptake that is supplied to symbiotic (plant) partners.
    [unitless]. This should only have a non-zero value for mycorrhizal fungi."""
    symbiote_phosphorus_uptake_fraction: float = Field(ge=0.0, le=1.0)
    """Fraction of nitrogen uptake that is supplied to symbiotic (plant) partners.
    [unitless]. This should only have a non-zero value for mycorrhizal fungi."""

    synthesis_nutrient_ratios: dict[str, float] = Field(init=False)
    """Average carbon nutrient ratios of the newly synthesised biomass [unitless].
    Microbes synthesis biomass for three different purposes: cell growth, extra-cellular
    enzyme production and in some cases fungal fruiting body production. The
    stoichiometry of each of these types of biomass is different, so the average
    stoichiometry of the biomass produced by each microbial group needs to be
    calculated.
    """

    @model_validator(mode="after")
    def _only_fungi_fruit(self) -> SoilMicrobe:
        if self.taxonomic_group != "fungi" and self.reproductive_allocation > 0:
            raise ValueError(
                "Reproductive allocation for non fungal groups must be zero."
            )

        return self

    @model_validator(mode="after")
    def _only_mycorrhiza_are_symbiotes(self) -> SoilMicrobe:
        if self.name not in ["ectomycorrhiza", "arbuscular_mycorrhiza"] and (
            self.symbiote_nitrogen_uptake_fraction > 0
            or self.symbiote_phosphorus_uptake_fraction > 0
        ):
            raise ValueError(
                "Non-mycorrhizal groups should allocate zero nutrient uptake to "
                "symbiotic partners!"
            )

        return self

    @computed_field(repr=False)  # type: ignore[prop-decorator]
    @cached_property
    def enzyme_production(self) -> dict[str, float]:
        """Full details of the enzymes produced by the microbial group.

        The keys are the substrates for which enzymes are produced, and the values are
        the allocation to enzyme production. This allocation is expressed as a fraction
        of the (gross) cellular biomass growth.
        """
        return {
            substrate: getattr(self, f"enzyme_production_{substrate}")
            for substrate in get_args(SUBSTRATES)
        }

    @computed_field(repr=False)  # type: ignore[prop-decorator]
    @cached_property
    def enzyme_substrates(self) -> list[str]:
        """Substrates that the microbial group produces enzymes for."""

        return [
            substrate
            for substrate, production in self.enzyme_production.items()
            if production > 0.0
        ]

    def __post_init__(self, enzyme_classes: dict[str, SoilEnzyme]) -> None:
        """Populate the ``SoilMicrobe`` instance.

        This method populates the ``SoilMicrobe`` attributes that require information
        about the enzymes included in the soil model.

        Args:
            enzyme_classes: The full set of parameters for all enzymes included in the
                soil model.
        """

        self.synthesis_nutrient_ratios = calculate_new_biomass_average_nutrient_ratios(
            taxonomic_group=self.taxonomic_group,
            c_n_ratio=self.c_n_ratio,
            c_p_ratio=self.c_p_ratio,
            enzyme_production=self.enzyme_production,
            reproductive_allocation=self.reproductive_allocation,
            enzyme_classes=enzyme_classes,
        )


def load_microbes(
    path: Path, enzyme_classes: dict[str, SoilEnzyme]
) -> dict[str, SoilMicrobe]:
    """Load and validate a soil microbial parameters CSV file.

    Args:
        path: Path to csv file containing parametrisation for the required soil
            microbial groups.
        enzyme_classes: Details of the soil enzyme parametrisation, which are needed to
            fully parameterise the microbial groups

    Raises:
        ValueError: If the path doesn't point to a readable csv file, or if that csv
            file is missing headers, contains surplus headers, is missing required
            microbial groups, contains duplicate microbial groups or contains microbial
            groups that aren't expected by the simulation.

    Returns:
        The full set of microbial groups required by the soil model.
    """

    try:
        data = pd.read_csv(path)
    except (FileNotFoundError, IsADirectoryError):
        raise ValueError(f"Microbial group CSV path not found or a directory: {path}")
    except pd.errors.ParserError as excep:
        raise ValueError(f"Could not parse microbe data from: {path}: {excep!s}")

    try:
        microbes = [
            SoilMicrobe(**rec, enzyme_classes=enzyme_classes)
            for rec in data.to_dict(orient="records")
        ]
    except ValidationError as excep:
        raise ValueError(f"Invalid data in microbe parametrisation CSV file: {excep!s}")

    # Check the set of microbes for duplicates
    provided_microbes = [e.name for e in microbes]
    set_provided_microbes = set(provided_microbes)

    if len(set_provided_microbes) != len(provided_microbes):
        raise ValueError(
            "Duplicated microbial groups in microbial parametrisation data"
        )

    if not set_provided_microbes == set(get_args(REQUIRED_MICROBIAL_GROUPS)):
        raise ValueError(
            f"The microbial groups provided in the microbial groups definition file "
            f"({set_provided_microbes!r}) do not match the required set of microbial "
            f"groups ({REQUIRED_MICROBIAL_GROUPS!r})"
        )

    # Package into a dict and return
    return {r.name: r for r in microbes}


def calculate_new_biomass_average_nutrient_ratios(
    taxonomic_group: str,
    c_n_ratio: float,
    c_p_ratio: float,
    enzyme_production: dict[str, float],
    reproductive_allocation: float,
    enzyme_classes: dict[str, SoilEnzyme],
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
