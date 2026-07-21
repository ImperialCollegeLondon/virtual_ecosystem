"""The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule:

* Defines an extended :class:`~pyrealm.demography.flora.Flora` class to hold additional
  traits used in the Virtual Ecosystem and to add required computed and reference traits

* Provides a simple loader function with error checking for failure modes.
"""  # noqa: D415

from __future__ import annotations

import pandas as pd
from pydantic import computed_field, model_validator
from pyrealm.demography.flora import Flora

from virtual_ecosystem.models.plants.model_config import PlantsConfiguration


class VEFlora(Flora):
    """Extended plant functional trait definition.

    This class extends the basic pyrealm Flora definition to include the extra traits
    required for the Virtual Ecosystem.
    """

    # HACK pyrealm3 - extended class has mutable defaults. Somehow this is OK in the
    #      pyrealm definition of Flora , but not here. It might be better to have them
    #      as tuples throughout. See:
    #           https://github.com/ImperialCollegeLondon/pyrealm/issues/695

    # TODO - docstring these
    # ruff: disable[RUF012]
    p_foliage_for_reproductive_tissue: list[float] = [0.05]
    resp_rt: list[float] = [0.05]
    tau_rt: list[float] = [1.0]
    gpp_topslice: list[float] = [0.1]
    deadwood_c_n_ratio: list[float] = [60.7]
    deadwood_c_p_ratio: list[float] = [856.5]
    leaf_turnover_c_n_ratio: list[float] = [25.5]
    leaf_turnover_c_p_ratio: list[float] = [415.0]
    plant_reproductive_tissue_turnover_c_n_ratio: list[float] = [12.5]
    plant_reproductive_tissue_turnover_c_p_ratio: list[float] = [125.5]
    root_turnover_c_n_ratio: list[float] = [656.7]
    root_turnover_c_p_ratio: list[float] = [45.6]
    foliage_c_n_ratio: list[float] = [15.0]
    foliage_c_p_ratio: list[float] = [300.0]
    c_mass_fruit_flesh: list[float] = [5.0]
    c_mass_per_fruit_seed: list[float] = [1.0]
    seeds_per_fruit: list[int] = [2]
    # ruff: enable[RUF012]

    # Additional traits populated during validation - these hold the reference values
    # for lai and tau_f, which are modified by herbivory.

    # HACK pyrealm 3 - This doesn't really work properly with strict mode (which we want
    #      to use) and the enforcement of equal lengths for attributes. It works for
    #      now, but it probably makes more sense to add these directly after to Cohorts
    #      after running create_cohorts. Keep this for now.
    lai_base: None | list[float] = None
    tau_f_base: None | list[float] = None

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
    def fruit_flesh_fraction(self) -> list[float]:
        """Calculate the fruit flesh fraction from the fruit traits.

        The Flora properties are lists not arrays, so calculated by iteration.
        """

        return [
            cmf / (cmf + (cms * spf))
            for cmf, cms, spf in zip(
                self.c_mass_fruit_flesh,
                self.c_mass_per_fruit_seed,
                self.seeds_per_fruit,
            )
        ]


def get_flora_from_config(config: PlantsConfiguration) -> VEFlora:
    """Generate a Flora object from a Virtual Ecosystem configuration.

    Args:
        config: A validated PlantsConfiguration instance.

    Returns:
        A  populated :class:`VEFlora` instance.
    """

    # Read the file, handling file IO and parsing errors.
    try:
        flora = VEFlora.from_csv(config.pft_definitions_path)
    except (FileNotFoundError, pd.errors.ParserError) as excep:
        raise excep

    return flora
