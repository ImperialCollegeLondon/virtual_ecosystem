"""Configuration classes for the soil model."""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import ClassVar, Literal, get_args

import pandas as pd
from pydantic import Field, ValidationError, field_validator, model_validator

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


class SoilEnzymeClass(Configuration):
    """Soil enzyme constants."""

    source: HIGHER_TAXONOMIC_GROUPS
    """The higher microbial group which produces the enzyme."""
    substrate: SUBSTRATES
    """The substrate which the enzyme acts upon."""
    maximum_rate: float
    """The maximum rate of the enzyme at the reference temperature [day^-1]."""
    half_saturation_constant: float
    """The half saturation constant for the enzyme at the reference temperature. Units
    of [kg{C} m^-3]."""
    activation_energy_rate: float
    """Activation energy for enzyme rate with temperature [J Kelvin^-1]."""
    activation_energy_saturation: float
    """Activation energy for enzyme saturation with temperature [J Kelvin^-1]."""
    # TODO - This should change to Kelvin when we change the default units to Kelvin
    reference_temperature: float
    """The temperature that enzyme rate and saturation were measured at [Celsius]."""
    turnover_rate: float
    """The turnover rate of the enzyme [day^-1]."""
    c_n_ratio: float
    """Ratio of carbon to nitrogen for the enzyme [unitless]."""
    c_p_ratio: float
    """Ratio of carbon to phosphorus for the enzyme [unitless]."""


class SoilEnzymes(Configuration):
    """Root configuration class for the soil model."""

    _required_enzymes: ClassVar[set[tuple[HIGHER_TAXONOMIC_GROUPS, SUBSTRATES]]] = (
        REQUIRED_ENZYMES
    )
    """Required enzyme classes, provided as all pairs of higher taxon source and
    substrates."""

    enzyme_class_definition: dict[str, SoilEnzymeClass]
    """Definition of enzyme classes for soil model."""

    @field_validator("enzyme_class_definition")
    def _enforce_required_enzymes(
        cls, enzymes: dict[str, SoilEnzymeClass]
    ) -> dict[str, SoilEnzymeClass]:
        """Validates the provided sets of enzyme classes."""
        provided_enzymes = [(e.source, e.substrate) for e in enzymes.values()]
        set_provided_enzymes = set(provided_enzymes)

        if len(set_provided_enzymes) != len(provided_enzymes):
            raise ValueError(
                "Duplicated enzyme source/substrate combinations in enzyme data"
            )

        if not set_provided_enzymes == cls._required_enzymes:
            raise ValueError(
                f"The source/substrate pairs provided in enzyme class definitions "
                f"({provided_enzymes!r}) do not match the required set of pairs "
                f"({cls._required_enzymes!r})"
            )

        return enzymes


def load_enzymes(path: Path) -> SoilEnzymes:
    """Load and validate a soil enzyme CSV file."""

    # Try and load the data
    try:
        data = pd.read_csv(path)
    except (FileNotFoundError, IsADirectoryError):
        raise ValueError(f"Enzyme CSV path not found or a directory: {path}")
    except pd.errors.ParserError as excep:
        raise ValueError(f"Could not parse enzyme data from: {path}: {excep!s}")

    # Try and validate the data
    try:
        # Validate the CSV records
        enzymes = [
            SoilEnzymeClass.model_validate(rec)
            for rec in data.to_dict(orient="records")
        ]

        # Package into a dict for the wrapper class
        enzymes_dict = {f"{r.source}_{r.substrate}": r for r in enzymes}

        # Validate the whole enzyme model
        enzyme_model = SoilEnzymes.model_validate(
            {"enzyme_class_definition": enzymes_dict}
        )
    except ValidationError as excep:
        raise ValueError(f"Invalid data in enzyme CSV file: {excep!s}")

    return enzyme_model


def load_enzymes_2(path: Path) -> dict[str, SoilEnzymeClass]:
    """Load and validate a soil enzyme CSV file."""

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
            SoilEnzymeClass.model_validate(rec)
            for rec in data.to_dict(orient="records")
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


class SoilMicrobialGroup(Configuration):
    """Microbial functional group definitions."""

    name: REQUIRED_MICROBIAL_GROUPS
    """The name of the microbial group functional type."""
    taxonomic_group: HIGHER_TAXONOMIC_GROUPS
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
    """Half saturation uptake constant for labile inorganic phosphorus [kg{P} m^-3]."""
    turnover_rate: float
    """Microbial maintenance turnover rate at reference temperature [day^-1]."""
    activation_energy_turnover: float
    """Activation energy for microbial maintenance turnover rate [J Kelvin^-1]."""
    reference_temperature: float
    """The temperature that turnover and uptake rates were measured at [Celsius]."""
    c_n_ratio: float
    """Ratio of carbon to nitrogen in biomass [unitless]."""
    c_p_ratio: float
    """Ratio of carbon to phosphorus in biomass [unitless]."""
    enzyme_production: dict[str, float]
    """Details of the enzymes produced by the microbial group. The keys are the
    substrates for which enzymes are produced, and the values are the allocation to
    enzyme production. This allocation is expressed as a fraction of the (gross)
    cellular biomass growth.
    """
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

    @model_validator(mode="after")
    def _only_fungi_fruit(self) -> SoilMicrobialGroup:
        if self.taxonomic_group != "fungi" and self.reproductive_allocation > 0:
            raise ValueError(
                "Reproductive allocation for non fungal groups must be zero."
            )

        return self

    @model_validator(mode="after")
    def _only_mycorrhiza_are_symbiotes(self) -> SoilMicrobialGroup:
        if self.name not in ["ectomycorrhiza", "arbuscular_mycorrhiza"] and (
            self.symbiote_nitrogen_uptake_fraction > 0
            or self.symbiote_phosphorus_uptake_fraction > 0
        ):
            raise ValueError(
                "Non-mycorrhizal groups should allocate zero nutrient uptake to "
                "symbiotic partners!"
            )

        return self


class SoilMicrobes(Configuration):
    """Root configuration class for the soil model."""

    _required_microbial_groups: ClassVar[set[REQUIRED_MICROBIAL_GROUPS]] = {
        *get_args(REQUIRED_MICROBIAL_GROUPS)
    }
    """Required named microbial groups."""

    microbial_group_definition: list[SoilMicrobialGroup]
    """Definition of microbial groups for soil model."""

    @field_validator("microbial_group_definition")
    def _enforce_required_microbial_groups(
        cls, microbial_groups: list[SoilMicrobialGroup]
    ) -> list[SoilMicrobialGroup]:
        """Validates the provided sets of enzyme classes."""
        provided_groups = {g.name for g in microbial_groups}

        if not provided_groups == cls._required_microbial_groups:
            raise ValueError(
                f"The microbial group definitions ({provided_groups!r}) does not match "
                f"the required set ({cls._required_microbial_groups!r})"
            )

        return microbial_groups


def load_microbes(path: Path) -> SoilMicrobes:
    """Load and validate microbial groups."""

    try:
        data = pd.read_csv(path)
    except (FileNotFoundError, IsADirectoryError):
        raise ValueError(f"Microbial group CSV path not found or a directory: {path}")
    except pd.errors.ParserError as excep:
        raise ValueError(f"Could not parse microbe data from: {path}: {excep!s}")

    try:
        microbe_definitions = [
            SoilMicrobialGroup.model_validate(rec)
            for rec in data.to_dict(orient="records")
        ]
        return SoilMicrobes.model_validate(
            {"microbial_group_definition": microbe_definitions}
        )
    except ValidationError as excep:
        raise ValueError(f"Invalid data in microbe CSV file: {excep!s}")
