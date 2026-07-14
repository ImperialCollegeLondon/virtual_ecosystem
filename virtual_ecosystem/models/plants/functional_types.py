"""The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule:

* Defines an extended :class:`~pyrealm.demography.flora.Flora` class to hold additional
  traits used in the Virtual Ecosystem and to add required computed and reference traits

* Provides a simple loader with error checking for failure modes.
"""  # noqa: D415

from __future__ import annotations

from typing import ClassVar

import pandas as pd
from pydantic import computed_field, model_validator
from pyrealm.demography.flora import Flora

from virtual_ecosystem.models.plants.model_config import PlantsConfiguration


class VEFlora(Flora):
    """Extended plant functional trait definition.

    This class extends the basic pyrealm Flora definition to include the extra traits
    required for the Virtual Ecosystem.
    """

    # HACK pyrealm3 - mutable defaults. Somehow this is OK in the pyrealm definition of
    #      Flora , but not here. It might be better to have them as tuples throughout.
    #      See: https://github.com/ImperialCollegeLondon/pyrealm/issues/695
    # ruff: disable[RUF012]
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
        A tuple containing a populated :class:`pyrealm.demography.flora.Flora` instance
        and an :class:`ExtraTraitsPFT` instance.
    """

    # Read the file, handling file IO and parsing errors.
    try:
        flora = VEFlora.from_csv(config.pft_definitions_path)
    except (FileNotFoundError, pd.errors.ParserError) as excep:
        raise excep

    return flora


class ExtraTraitsPFT:  ## TODO pyrealm3 - kill this once Community rehashed.
    """A dataclass to hold additional traits for a plant functional type.

    This class is used to store traits that are not part of the standard PFT definition
    in Pyrealm, but are used in the Virtual Ecosystem. Each instance of this class maps
    to one PFT, keyed by the PFT name. The structure is:

    {'pft_name': {'trait_name': trait_value, ...},
     'pft_name_2': {'trait_name': trait_value, ...}, ...}
    """

    array_attrs: ClassVar[tuple[str, ...]] = (
        "deadwood_c_n_ratio",
        "deadwood_c_p_ratio",
        "leaf_turnover_c_n_ratio",
        "leaf_turnover_c_p_ratio",
        "plant_reproductive_tissue_turnover_c_n_ratio",
        "plant_reproductive_tissue_turnover_c_p_ratio",
        "root_turnover_c_p_ratio",
        "root_turnover_c_n_ratio",
        "foliage_c_n_ratio",
        "foliage_c_p_ratio",
        "c_mass_fruit_flesh",
        "c_mass_per_fruit_seed",
        "seeds_per_fruit",
    )
    """Additional array attributes accepted by the ExtraTraitsPFT class."""

    traits: dict[str, dict[str, float]]

    def __init__(self, traits: dict[str, dict[str, float]]):
        """Initialise the ExtraTraitsPFT instance with a dictionary of traits."""
        self.traits = traits

        # Calculate the fruit flesh fraction from the masses and seed number
        for pft in self.traits.keys():
            self.traits[pft]["fruit_flesh_fraction"] = self.traits[pft][
                "c_mass_fruit_flesh"
            ] / (
                self.traits[pft]["c_mass_fruit_flesh"]
                + (
                    self.traits[pft]["c_mass_per_fruit_seed"]
                    * self.traits[pft]["seeds_per_fruit"]
                )
            )

    @classmethod
    def _from_file_data(cls, input_traits: list) -> ExtraTraitsPFT:
        """Initialise the ExtraTraitsPFT instance.

        Args:
            input_traits: A list of dictionaries, where each dictionary represents
                traits for a plant functional type.
        """
        traits = {}
        for pft in input_traits:
            traits[pft["name"]] = {k: v for k, v in pft.items() if k != "name"}

        return cls(traits)

    @classmethod
    def from_df(cls, df) -> ExtraTraitsPFT:
        """Load additional traits from a DataFrame.

        Args:
            df: A pandas DataFrame containing additional traits.

        Returns:
            An instance of ExtraTraitsPFT with the loaded traits.
        """

        traits = df.to_dict(orient="records")

        return cls._from_file_data(traits)
