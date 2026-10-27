"""Configuration classes for the soil model."""

# TODO - THIS ONLY SHOULD STICK AROUND UNTIL I'VE MIGRATE EVERYTHING OVER TO ANOTHER
# MODULE
from __future__ import annotations

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
