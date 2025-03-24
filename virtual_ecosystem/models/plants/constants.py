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

    ppfd_to_dsr: float = 2.04
    """Convert from downward shortwave radiation to photosynthetic photon flux density.

    Converting units from umol m-2 s-1 to W m-2 (conversion = 4.57) and assuming 46% of
    DSR is photosynthetically active results in an overall conversion factor of 2.04.
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
