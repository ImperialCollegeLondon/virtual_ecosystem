"""The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule provides
functionality to load plant functional type definitions from the model configuration and
generate a :class:`~pyrealm.demography.flora.Flora` object for use in simulation.
"""  # noqa: D205

from __future__ import annotations

import pandas as pd
from pyrealm.demography.flora import Flora

from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


class ExtraTraitsPFT:
    """A dataclass to hold additional traits for a plant functional type.

    This class is used to store traits that are not part of the standard PFT definition
    in Pyrealm, but are used in the Virtual Ecosystem. Each instance of this class maps
    to one PFT, keyed by the PFT name. The structure is:

    {'pft_name': {'trait_name': trait_value, ...},
     'pft_name_2': {'trait_name': trait_value, ...}, ...}
    """

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


def get_flora_from_config(config: Config) -> tuple[Flora, ExtraTraitsPFT]:
    """Generate a Flora object from a Virtual Ecosystem configuration.

    Args:
        config: A validated Virtual Ecosystem model configuration object.

    Returns:
        A populated :class:`pyrealm.demography.flora.Flora` instance
    """

    extra_traits = [
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
    ]

    if "plants" not in config:
        msg = "Model configuration for plants model not found."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # Check for duplicate definition options - this should be prevented by the schema
    # definition setting oneOf the following two is required
    if (
        "pft_definition" in config["plants"]
        and "pft_definitions_path" in config["plants"]
    ):
        msg = "Do not use both `pft_definitions_path` and `pft_definition` in config."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # If the data is provided in the configuration, load that
    if "pft_definition" in config["plants"]:
        # TODO: currently need to rename this property to match internal expectation in
        # pyrealm, change here if this is fixed/aligned.

        extra_traits_data = [
            {k: v for k, v in d.items() if k in extra_traits or k == "name"}
            for d in config["plants"]["pft_definition"]
        ]

        pft_traits = [
            {k: v for k, v in d.items() if k not in extra_traits}
            for d in config["plants"]["pft_definition"]
        ]

        extra_traits_model = ExtraTraitsPFT._from_file_data(extra_traits_data)

        pft_data = {"pft": pft_traits}
        return Flora._from_file_data(pft_data), extra_traits_model

    try:
        df = pd.read_csv(config["plants"]["pft_definitions_path"])
    except (FileNotFoundError, pd.errors.ParserError) as excep:
        raise excep

    extra_traits_columns = [*extra_traits, "name"]
    extra_traits_data = df[extra_traits_columns]
    extra_traits_model = ExtraTraitsPFT.from_df(df=extra_traits_data)
    pft_traits = df.drop(columns=extra_traits)
    pft_data = {"pft": pft_traits.to_dict(orient="records")}

    return Flora._from_file_data(pft_data), extra_traits_model
