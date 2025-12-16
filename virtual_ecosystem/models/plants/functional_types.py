"""The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule provides
functionality to load plant functional type definitions from the model configuration and
generate a :class:`~pyrealm.demography.flora.Flora` object for use in simulation.
"""  # noqa: D205

from __future__ import annotations

from typing import ClassVar

import pandas as pd
from pyrealm.demography.flora import Flora

from virtual_ecosystem.models.plants.model_config import PlantsConfiguration


class ExtraTraitsPFT:
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
    )
    """Additional array attributes accepted by the ExtraTraitsPFT class."""

    traits: dict[str, dict[str, float]]

    def __init__(self, traits: dict[str, dict[str, float]]):
        """Initialise the ExtraTraitsPFT instance with a dictionary of traits."""
        self.traits = traits

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


def get_flora_from_config(config: PlantsConfiguration) -> tuple[Flora, ExtraTraitsPFT]:
    """Generate a Flora object from a Virtual Ecosystem configuration.

    Args:
        config: A validated PlantsConfiguration instance.

    Returns:
        A tuple containing a populated :class:`pyrealm.demography.flora.Flora` instance
        and an :class:`ExtraTraitsPFT` instance.
    """

    # Read the file, handling file IO and parsing errors.
    try:
        df = pd.read_csv(config.pft_definitions_path)
    except (FileNotFoundError, pd.errors.ParserError) as excep:
        raise excep

    # Split into pyrealm PFT traits and VE extra traits
    extra_traits_columns = [*ExtraTraitsPFT.array_attrs, "name"]
    extra_traits_data = df[extra_traits_columns]
    extra_traits_model = ExtraTraitsPFT.from_df(df=extra_traits_data)
    pft_traits = df.drop(columns=list(ExtraTraitsPFT.array_attrs))
    pft_data = {"pft": pft_traits.to_dict(orient="records")}

    return Flora._from_file_data(pft_data), extra_traits_model
