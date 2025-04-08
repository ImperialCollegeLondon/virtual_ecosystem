"""The ``models.soil.microbial_groups`` module contains the classes needed to define
the different microbial functional groups used in the soil model.
"""  # noqa: D205

from dataclasses import dataclass
from typing import Any

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

    enzyme_production: dict[str, float]
    """Details of the enzymes produced by the microbial group.
    
    The keys are the substrates for which enzymes are produced, and the values are the
    allocation to enzyme production. This allocation is expressed as a fraction of the
    (gross) cellular biomass growth.
    """

    synthesis_nutrient_ratios: dict[str, float]
    """Average carbon to nutrient ratios for the total synthesised biomass.
    
    Microbes have to synthesis both cellular biomass and extracellular enzymes. We
    assume that this occurs in fixed unvarying proportion. This attribute stores the
    carbon nutrient (nitrogen, phosphorus) ratios for the total synthesised biomass.
    """

    @classmethod
    def build_microbial_group(
        cls, group_config: dict[str, Any], enzyme_classes: dict[str, EnzymeConstants]
    ):
        """Class method to build the microbial group including enzyme information.

        Args:
            group_config: The config details for microbial group in question.
            enzyme_classes: Details of the enzyme classes used by the soil model.
        """

        return cls(
            **group_config,
            synthesis_nutrient_ratios=calculate_new_biomass_average_nutrient_ratios(
                name=group_config["name"],
                c_n_ratio=group_config["c_n_ratio"],
                c_p_ratio=group_config["c_p_ratio"],
                enzyme_production=group_config["enzyme_production"],
                enzyme_classes=enzyme_classes,
            ),
        )

    def find_enzyme_substrates(self) -> list[str]:
        """Substrates that the microbial group produces enzymes for."""

        return [
            substrate
            for substrate, production in self.enzyme_production.items()
            if production > 0.0
        ]


def calculate_new_biomass_average_nutrient_ratios(
    name: str,
    c_n_ratio: float,
    c_p_ratio: float,
    enzyme_production: dict[str, float],
    enzyme_classes: dict[str, EnzymeConstants],
) -> dict[str, float]:
    """Calculate average carbon nutrient ratios of the newly synthesised biomass.

    Microbes have to synthesise cellular biomass as well as extracellular enzymes. This
    method calculates average nutrient ratio of this total biomass synthesis by
    calculating the average weighted by the relative production allocation to each
    enzyme class and cellular growth.

    Args:
        name: Name of the microbial group.
        c_n_ratio: Ratio of carbon to nitrogen for the microbial group's cellular
            biomass.
        c_p_ratio: Ratio of carbon to nitrogen for the microbial group's cellular
            biomass.
        enzyme_production: Details of the enzymes produced by the microbial group, i.e.
            which substrates are enzymes produced for, and how much (relative to
            cellular synthesis)
        enzyme_classes: Details of the enzyme classes used by the soil model.
    """

    enzyme_c_n_weighted = sum(
        enzyme_classes[f"{name}_{substrate}"].c_n_ratio * allocation
        for substrate, allocation in enzyme_production.items()
    )

    enzyme_c_p_weighted = sum(
        enzyme_classes[f"{name}_{substrate}"].c_p_ratio * allocation
        for substrate, allocation in enzyme_production.items()
    )

    total_enzyme_allocation = sum(enzyme_production.values())

    return {
        "nitrogen": (c_n_ratio + enzyme_c_n_weighted) / (1.0 + total_enzyme_allocation),
        "phosphorus": (c_p_ratio + enzyme_c_p_weighted)
        / (1.0 + total_enzyme_allocation),
    }


def make_full_set_of_microbial_groups(
    config: Config, enzyme_classes: dict[str, EnzymeConstants]
) -> dict[str, MicrobialGroupConstants]:
    """Make the full set of functional groups used in the soil model.

    Args:
        config: The complete virtual ecosystem config.
        enzyme_classes: Details of the enzyme classes used by the soil model.

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
        group_name: MicrobialGroupConstants.build_microbial_group(
            group_config=next(
                functional_group
                for functional_group in config["soil"]["microbial_group_definition"]
                if functional_group["name"] == group_name
            ),
            enzyme_classes=enzyme_classes,
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
