"""This submodule contains a set of dataclasses containing constants used
in the :mod:`~virtual_ecosystem.models.plants` module.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class PlantsConsts(ConstantsDataclass):
    """Constants for the :mod:`~virtual_ecosystem.models.plants` model."""

    per_stem_annual_mortality_probability: float = 0.1
    """Basic annual mortality rate for plants."""

    dsr_to_ppfd: float = 2.04
    """Convert from downward shortwave radiation to photosynthetic photon flux density.

    Converting DSR in W m-2 to PPFD in µmol m-2 s-1. 1 W m-2 of sunlight is roughly 4.57
    µmol m-2 s-1 of full spectrum sunlight, of which about 4.57 * 46% = 2.04  µmol m-2
    s-1 is PPFD.
    """

    stem_lignin: float = 0.545
    """Fraction of stem biomass that is lignin."""

    senesced_leaf_lignin: float = 0.05
    """Fraction of senesced leaf biomass that is lignin."""

    leaf_lignin: float = 0.10
    """Fraction of leaf biomass that is lignin."""

    plant_reproductive_tissue_lignin: float = 0.01
    """Fraction of plant reproductive tissue biomass that is lignin."""

    root_lignin: float = 0.20
    """Fraction of root biomass that is lignin."""

    deadwood_c_n_ratio: float = 56.5
    """Carbon to Nitrogen ratio of deadwood."""

    leaf_turnover_c_n_ratio: float = 25.5
    """Carbon to Nitrogen ratio of leaf turnover."""

    plant_reproductive_tissue_turnover_c_n_ratio: float = 12.5
    """Carbon to Nitrogen ratio of plant reproductive tissue turnover."""

    root_turnover_c_n_ratio: float = 45.6
    """Carbon to Nitrogen ratio of root turnover."""

    deadwood_c_p_ratio: float = 856.5
    """Carbon to Phosphorous ratio of deadwood."""

    leaf_turnover_c_p_ratio: float = 415.0
    """Carbon to Phosphorous ratio of leaf turnover."""

    plant_reproductive_tissue_turnover_c_p_ratio: float = 125.5
    """Carbon to Phosphorous ratio of plant reproductive tissue turnover."""

    root_turnover_c_p_ratio: float = 656.7
    """Carbon to Phosphorous ratio of root turnover."""

    subcanopy_extinction_coef: float = 0.5
    """The extinction coefficient of subcanopy vegetation (unitless)."""

    subcanopy_specific_leaf_area: float = 14
    """The specific leaf area of subcanopy vegetation (m2 kg-1)."""

    subcanopy_respiration_fraction: float = 0.1
    """The fraction of gross primary productivity used in respiration (unitless)."""

    subcanopy_yield: float = 0.6
    """The yield fraction of net primary productivity in subcanopy vegetation
    (unitless). """

    subcanopy_reproductive_allocation: float = 0.1
    """The fraction of subcanopy net primary productivity that is allocated to subcanopy
    seedbank mass (unitless)."""

    subcanopy_sprout_rate: float = 0.1
    """The rate at which new subcanopy biomass sprouts from the subcanopy seedbank mass
    (kg kg-1 m-2 y-1)."""

    subcanopy_sprout_yield: float = 0.5
    """The fraction of subcanopy seedbank mass that is realised as subcanopy vegetation
    mass (kg kg-1)."""
    root_exudates: float = 0.5
    """Fraction of GPP topslice allocated to root exudates."""

    propagule_mass_portion: float = 0.5
    """Fraction of reprodutive tissue allocated to propagules."""

    carbon_mass_per_propagule: float = 1
    """Mass of carbon per propagule in g."""
