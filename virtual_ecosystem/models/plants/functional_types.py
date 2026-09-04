"""The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule:

* Defines an extended :class:`~pyrealm.demography.flora.Flora` class to hold additional
  traits used in the Virtual Ecosystem and to add required computed and reference traits

* Provides a simple loader function with error checking for failure modes.
"""  # noqa: D415

from __future__ import annotations

import pandas as pd
from pydantic import ConfigDict, computed_field, model_validator
from pyrealm.demography.flora import Flora, FloraValidator, load_flora_from_csv

from virtual_ecosystem.models.plants.model_config import PlantsConfiguration


class VEFloraValidator(FloraValidator):
    """Extended plant functional trait definition.

    This class extends the basic pyrealm Flora definition to include the extra traitsp
    required for the Virtual Ecosystem.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    fruit_seed_foliage_mass_fraction: tuple[float, ...] = (0.05,)
    r"""Defines the initial carbon allocation to reproductive structures (fruit and
     seed) from net primary productivity as a fraction of the initial individual canopy
     carbon mass (kg kg-1)."""
    resp_rt: tuple[float, ...] = (0.05,)
    r"""The annual respiration rate of reproductive tissues (:math:`r_{rt}`, kg
     kg-1)."""
    tau_rt: tuple[float, ...] = (1.0,)
    r"""The annual turnover rate of reproductive tissues (:math:`\tau_{rt}`, kg
     kg-1)."""
    root_symbiote_npp_fraction: tuple[float, ...] = (0.1,)
    r"""Carbon allocation to root symbiotes as a fraction of net primary productivity
     (kg kg-1)."""
    stem_c_n_ratio: tuple[float, ...] = (60.7,)
    r"""Carbon/Nitrogen ratio of stem tissue (kg kg-1)."""
    stem_c_p_ratio: tuple[float, ...] = (856.5,)
    r"""Carbon/Phosphorous ratio of stem tissue (kg kg-1)."""
    foliage_turnover_c_n_ratio: tuple[float, ...] = (25.5,)
    r"""Carbon/Nitrogen ratio of leaf turnover, following nutrient reabsorption during
     leaf senescence (kg kg-1)."""
    foliage_turnover_c_p_ratio: tuple[float, ...] = (415.0,)
    r"""Carbon/Phosphorous ratio of leaf turnover, following nutrient reabsorption
     during leaf senescence (kg kg-1)."""
    fruit_seed_c_n_ratio: tuple[float, ...] = (12.5,)
    r"""Carbon/Nitrogen ratio of reproductive structures (fruit tissue and seeds) (kg
     kg-1)."""
    fruit_seed_c_p_ratio: tuple[float, ...] = (125.5,)
    r"""Carbon/Phosphorous ratio of reproductive structures (fruit tissue and seeds) (kg
     kg-1)."""
    root_c_n_ratio: tuple[float, ...] = (656.7,)
    r"""Carbon/Nitrogen ratio of fine root tissue (kg kg-1)."""
    root_c_p_ratio: tuple[float, ...] = (45.6,)
    r"""Carbon/Phosphorous ratio of fine root tissue (kg kg-1)."""
    foliage_c_n_ratio: tuple[float, ...] = (15.0,)
    r"""Carbon/Nitrogen ratio of active leaf tissue (kg kg-1)."""
    foliage_c_p_ratio: tuple[float, ...] = (300.0,)
    r"""Carbon/Phosphorous ratio of active leaf tissue (kg kg-1)."""
    c_mass_fruit_flesh: tuple[float, ...] = (5.0,)
    r"""Carbon mass of total fruit flesh in reproductive structures (grams)."""
    c_mass_per_fruit_seed: tuple[float, ...] = (1.0,)
    r"""Carbon mass of individual seeds in reproductive structures (grams)."""
    seeds_per_fruit: tuple[int, ...] = (2,)
    r"""Number of seeds in each reproductive structure (unitless)."""

    # Additional traits populated during validation - these hold the reference values
    # for lai and tau_f, which are modified by herbivory.

    # HACK pyrealm 3 - This doesn't really work properly with strict mode (which we want
    #      to use) and the enforcement of equal lengths for attributes. It works for
    #      now, but it probably makes more sense to add these directly after to Cohorts
    #      after running create_cohorts. Keep this for now.
    lai_base: tuple[float, ...] | None = None
    r"""Reference variable holding the base LAI for the PFT."""
    tau_f_base: tuple[float, ...] | None = None
    r"""Reference variable holding the base foliage turnover rate for the PFT."""

    @model_validator(mode="before")
    @classmethod
    def populate_reference_values(cls, data, info):
        """Populate the reference value fields from the imported data."""
        data["lai_base"] = data.get("lai")
        data["tau_f_base"] = data.get("tau_f")

        return data

    # This decorator order for computed fields is recommended by pydantic but mypy
    # objects, so mute the warnings.

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fruit_flesh_fraction(self) -> tuple[float, ...]:
        """The proportion of fleshy tissue in reproductive structures, calculated
        automatically from  fruit flesh fraction from the fruit traits.
        """  # noqa: D205
        # The Flora properties are lists not arrays, so calculated by iteration.

        return tuple(
            [
                cmf / (cmf + (cms * spf))
                for cmf, cms, spf in zip(
                    self.c_mass_fruit_flesh,
                    self.c_mass_per_fruit_seed,
                    self.seeds_per_fruit,
                )
            ]
        )


def get_flora_from_config(config: PlantsConfiguration) -> Flora:
    """Generate a Flora object from a Virtual Ecosystem configuration.

    Args:
        config: A validated PlantsConfiguration instance.

    Returns:
        A  populated :class:`pyrealm.demography.flora.Flora` instance.
    """

    # Read the file, handling file IO and parsing errors.
    try:
        flora = load_flora_from_csv(
            path=config.pft_definitions_path, strict=True, validator=VEFloraValidator
        )
    except (FileNotFoundError, pd.errors.ParserError) as excep:
        raise excep

    return flora
