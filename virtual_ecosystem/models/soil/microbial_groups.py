"""The ``models.soil.microbial_groups`` module contains the classes needed to define
the different microbial functional groups used in the soil model.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


@dataclass(frozen=True)
class EnzymeConstants:
    """Container for the set of constants associated with a specific enzyme."""

    source: str
    """The microbial group which produces the enzyme."""

    substrate: str
    """The substrate which the enzyme acts upon."""

    maximum_rate: float
    """The maximum rate of the enzyme at the reference temperature [day^-1]."""

    half_saturation_constant: float
    """The half saturation constant for the enzyme at the reference temperature.

    Units of [kg C m^-3]."""

    activation_energy_rate: float
    """Activation energy for enzyme rate with temperature [J K^-1]."""

    activation_energy_saturation: float
    """Activation energy for enzyme saturation with temperature [J K^-1]."""

    # TODO - This should change to Kelvin when we change the default units to Kelvin
    reference_temperature: float
    """The reference temperature that enzyme rate and saturation were measured at [C].
    """

    turnover_rate: float
    """The turnover rate of the enzyme [day^-1]."""

    c_n_ratio: float
    """Ratio of carbon to nitrogen for the enzyme [unitless]."""

    c_p_ratio: float
    """Ratio of carbon to phosphorus for the enzyme [unitless]."""


@dataclass(frozen=True)
class MicrobialGroupConstants:
    """Container for the set of constants associated with a microbial functional group.

    This sets out the constants which must be defined for each microbial functional
    group.
    """

    name: str
    """The name of the microbial group functional type."""

    max_uptake_rate_labile_C: float
    """Maximum rate at the reference temperature of labile carbon uptake [day^-1]."""

    activation_energy_uptake_rate: float
    """Activation energy for nutrient uptake [J K^-1]."""

    half_sat_labile_C_uptake: float
    """Half saturation constant for uptake of labile carbon (LMWC) [kg C m^-3]."""

    activation_energy_uptake_saturation: float
    """Activation energy for nutrient uptake saturation constants [J K^-1]."""

    max_uptake_rate_ammonium: float
    """Maximum possible rate for ammonium uptake [day^-1]."""

    half_sat_ammonium_uptake: float
    """Half saturation constant for uptake of ammonium [kg N m^-3]."""

    max_uptake_rate_nitrate: float
    """Maximum possible rate for nitrate uptake [day^-1]."""

    half_sat_nitrate_uptake: float
    """Half saturation constant for uptake of nitrate [kg N m^-3]."""

    max_uptake_rate_labile_p: float
    """Maximum possible rate for labile inorganic phosphorus uptake [day^-1]."""

    half_sat_labile_p_uptake: float
    """Half saturation constant for uptake of labile inorganic phosphorus [kg P m^-3].
    """

    turnover_rate: float
    """Microbial maintenance turnover rate at reference temperature [day^-1]."""

    activation_energy_turnover: float
    """Activation energy for microbial maintenance turnover rate [J K^-1]."""

    reference_temperature: float
    """The reference temperature that turnover and uptake rates were measured at [C].
    """

    c_n_ratio: float
    """Ratio of carbon to nitrogen in biomass [unitless]."""

    c_p_ratio: float
    """Ratio of carbon to phosphorus in biomass [unitless]."""


def make_full_set_of_microbial_groups(
    config: Config,
) -> dict[str, MicrobialGroupConstants]:
    """Make the full set of functional groups used in the soil model.

    Args:
        config: The complete virtual ecosystem config.

    Raises:
        ConfigurationError: If the soil model configuration is missing, if expected
            functional groups are not defined, or if unexpected functional groups are
            defined.

    Returns:
        A dictionary containing each functional group used in the soil model (currently
        bacteria and fungi).
    """

    if "soil" not in config:
        msg = "Model configuration for soil model not found."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    expected_groups = {"fungi", "bacteria"}
    defined_groups = {
        group["name"] for group in config["soil"]["microbial_group_definition"]
    }

    undefined_groups = expected_groups.difference(defined_groups)
    unexpected_groups = defined_groups.difference(expected_groups)
    if undefined_groups:
        msg = (
            "The following expected soil microbial groups are not defined: "
            f"{', '.join(undefined_groups)}"
        )
        LOGGER.critical(msg)
    if unexpected_groups:
        msg = (
            "The following microbial groups are not valid: "
            f"{', '.join(unexpected_groups)}"
        )
        LOGGER.critical(msg)
    if undefined_groups or unexpected_groups:
        raise ConfigurationError(
            "The soil microbial group configuration contains errors. Please check the "
            "log."
        )

    return {
        group_name: MicrobialGroupConstants(
            **next(
                functional_group
                for functional_group in config["soil"]["microbial_group_definition"]
                if functional_group["name"] == group_name
            )
        )
        for group_name in expected_groups
    }


def make_full_set_of_enzymes(
    config: Config,
) -> dict[str, EnzymeConstants]:
    """Make the full set of enzyme classes used in the soil model.

    Args:
        config: The complete virtual ecosystem config.

    Raises:
        ConfigurationError: If the soil model configuration is missing, if expected
            enzyme classes are not defined, or if unexpected enzyme classes are
            defined.

    Returns:
        A dictionary containing each enzyme class used in the soil model.
    """

    if "soil" not in config:
        msg = "Model configuration for soil model not found."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    expected_classes = {
        ("fungi", "pom"),
        ("fungi", "maom"),
        ("bacteria", "pom"),
        ("bacteria", "maom"),
    }
    defined_classes = {
        (group["source"], group["substrate"])
        for group in config["soil"]["enzyme_class_definition"]
    }

    undefined_classes = expected_classes.difference(defined_classes)
    unexpected_classes = defined_classes.difference(expected_classes)
    if undefined_classes:
        msg = "The following expected enzyme classes are not defined: " + ", ".join(
            f"{source}_{substrate}" for source, substrate in undefined_classes
        )
        LOGGER.critical(msg)
    if unexpected_classes:
        msg = "The following enzyme classes are not valid: " + ", ".join(
            f"{source}_{substrate}" for source, substrate in unexpected_classes
        )
        LOGGER.critical(msg)
    if undefined_classes or unexpected_classes:
        raise ConfigurationError(
            "The soil enzyme classes configuration contains errors. Please check the "
            "log."
        )

    return {
        f"{microbe}_{substrate}": EnzymeConstants(
            **next(
                enzyme_class
                for enzyme_class in config["soil"]["enzyme_class_definition"]
                if enzyme_class["source"] == microbe
                and enzyme_class["substrate"] == substrate
            )
        )
        for (microbe, substrate) in expected_classes
    }
