"""This submodule contains a set of dataclasses containing constants used
in the :mod:`~virtual_ecosystem.models.plants` module.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class PlantsConsts(ConstantsDataclass):
    """Constants for the :mod:`~virtual_ecosystem.models.plants` model."""

    per_stem_annual_mortality_rate: float = 0.1
    """Basic annual mortality rate for plants."""

    percent_stem_mass_attributed_to_lignin: float = 0.25
    """Fraction of stem mass attributed to lignin.
    
    This value can vary from species to species, but here is assumed to be 25% for all
    plants.
    """

    ppfd_to_dsr: float = 2.04
    """Convert from downward shortwave radiation to photosynthetic photon flux density.

    Converting units from umol m-2 s-1 to W m-2 (conversion = 4.57) and assuming 46% of
    DSR is photosynthetically active results in an overall conversion factor of 2.04.
    """
