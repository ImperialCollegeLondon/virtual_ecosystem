"""The `models.animals.constants` module contains a set of dictionaries containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module

The near-future intention is to rework the relationship between these constants and the
AnimalCohort objects in which they are used such that there is a FunctionalType class
in-between them. This class will hold the specific scaling, rate, and conversion
parameters required for determining the function of a specific AnimalCohort and will
avoid frequent searches through this constants file for values.
"""  # noqa: D205, D415

from typing import NamedTuple


class Taxon(NamedTuple):
    """Simple taxon object."""

    endotherm_metabolic_rates: tuple[float, float]
    damuths_law_terms: tuple[float, float]
    fat_mass_terms: tuple[float, float]
    muscle_mass_terms: tuple[float, float]
    intake_rate_terms: tuple[float, float]
    energy_density: float
    conversion_efficiency: float


MAMMALIAN_HERBIVORE = Taxon(
    endotherm_metabolic_rates=(0.75, 0.047),
    damuths_law_terms=(-0.75, 4.23),
    fat_mass_terms=(1.19, 0.02),
    muscle_mass_terms=(1.0, 0.38),
    intake_rate_terms=(0.71, 0.63),
    energy_density=7000.0,
    conversion_efficiency=0.1,
)

MAMMALIAN_CARNIVORE = Taxon(
    endotherm_metabolic_rates=(0.75, 0.047),
    damuths_law_terms=(-0.75, 1.00),
    fat_mass_terms=(1.19, 0.02),
    muscle_mass_terms=(1.0, 0.38),
    intake_rate_terms=(0.71, 0.63),
    energy_density=7000.0,
    conversion_efficiency=0.25,
)

AVIAN_HERBIVORE = Taxon(
    endotherm_metabolic_rates=(0.75, 0.05),
    damuths_law_terms=(-0.75, 5.00),
    fat_mass_terms=(1.19, 0.05),
    muscle_mass_terms=(1.0, 0.40),
    intake_rate_terms=(0.7, 0.50),
    energy_density=7000.0,
    conversion_efficiency=0.25,
)

AVIAN_CARNIVORE = Taxon(
    endotherm_metabolic_rates=(0.75, 0.05),
    damuths_law_terms=(-0.75, 2.00),
    fat_mass_terms=(1.19, 0.05),
    muscle_mass_terms=(1.0, 0.40),
    intake_rate_terms=(0.7, 0.50),
    energy_density=7000.0,
    conversion_efficiency=0.1,
)
