"""The ``models.abiotic.constants`` module contains a set of dataclasses which contain
parameters required by the broader :mod:`~virtual_rainforest.models.abiotic` model.
These parameters are constants in that they should not be changed during a particular
simulation.
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `abiotic` model."""

    specific_heat_equ_factor_1: float = 2e-05
    """Factor in calculation of molar specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`."""

    specific_heat_equ_factor_2: float = 0.0002
    """Factor in calculation of molar specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`."""

    latent_heat_vap_equ_factor_1: float = 1.91846e6
    """Factor in calculation of latent heat of vaporisation.

    Implementation after :cite:t:`maclean_microclimc_2021`, value is taken from
    :cite:t:`henderson-sellers_new_1984`.
    """
    latent_heat_vap_equ_factor_2: float = 33.91
    """Factor in calculation of latent heat of vaporisation.

    Implementation after :cite:t:`maclean_microclimc_2021`, value is taken from
    :cite:t:`henderson-sellers_new_1984`.
    """
