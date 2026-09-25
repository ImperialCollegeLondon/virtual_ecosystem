"""The :mod:`~virtual_ecosystem.models.palms.functional_types` submodule:

* Extends :class:`~virtual_ecosystem.models.plants.functional_types.VEFloraValidator`
  with the additional traits required by the palm growth form equations in
  :mod:`~virtual_ecosystem.models.palms.palms`.

* Provides a loader function with error checking for failure modes, analogous to
  :func:`~virtual_ecosystem.models.plants.functional_types.get_flora_from_config`.

This validator is kept standalone rather than folded into the shared
:class:`~virtual_ecosystem.models.plants.functional_types.VEFloraValidator` because
pyrealm's strict flora validation requires every trait with a default value to be
explicitly present in the input PFT CSV data. Adding palm-only traits to the shared
validator would therefore require every tree PFT CSV in the repository to also define
them. Standalone palm PFT definitions keep the existing tree PFT CSV data and formats
unchanged while palms is validated separately.
"""  # noqa: D415

import pandas as pd
from pyrealm.demography.flora import Flora, load_flora_from_csv

from virtual_ecosystem.models.palms.model_config import PalmsConfiguration
from virtual_ecosystem.models.plants.functional_types import VEFloraValidator


class PalmFloraValidator(VEFloraValidator):
    """Extended plant functional trait definition for palms.

    This class extends :class:`~virtual_ecosystem.models.plants.functional_types.
    VEFloraValidator` to include the additional traits required by the palm growth
    form equations in :mod:`~virtual_ecosystem.models.palms.palms`.
    """

    palm_a: tuple[float, ...] = (1.1444,)
    r"""Placeholder palm allometry parameter (:math:`a`), pending a permanent name."""
    palm_b: tuple[float, ...] = (0.2455,)
    r"""Placeholder palm allometry parameter (:math:`b`), pending a permanent name."""
    palm_stem_resp_fraction: tuple[float, ...] = (0.65,)
    r"""Fraction of palm stem tissue mass used to calculate stem respiration."""


def get_flora_from_config(config: PalmsConfiguration) -> Flora:
    """Generate a Flora object from a Virtual Ecosystem palms configuration.

    Args:
        config: A validated PalmsConfiguration instance.

    Returns:
        A populated :class:`pyrealm.demography.flora.Flora` instance.
    """

    # Read the file, handling file IO and parsing errors.
    try:
        flora = load_flora_from_csv(
            path=config.pft_definitions_path,
            strict=True,
            validator=PalmFloraValidator,
        )
    except (FileNotFoundError, pd.errors.ParserError) as excep:
        raise excep

    return flora
