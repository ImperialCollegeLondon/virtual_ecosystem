"""The ``models.soil.microbial_groups`` module contains the classes needed to define
the different microbial functional groups used in the soil model.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.models.soil.constants import SoilConsts


@dataclass(frozen=True)
class MicrobialGroupConstants:
    """Container for the set of constants associated with a microbial functional group.

    This sets out the constants which must be defined for each microbial functional
    group.
    """

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

    c_n_ratio: float
    """Ratio of carbon to nitrogen in biomass [unitless]."""

    c_p_ratio: float
    """Ratio of carbon to phosphorus in biomass [unitless]."""


def make_full_set_of_microbial_groups(
    constants: SoilConsts,
) -> dict[str, MicrobialGroupConstants]:
    """Make the full set of functional groups used in the soil model.

    Args:
        constants: The constants for the soil model.

    Returns:
        A dictionary containing each functional group used in the soil model (currently
        bacteria and fungi).
    """

    return {
        "bacteria": make_bacterial_functional_group(constants),
        "fungi": make_fungal_functional_group(constants),
    }


def make_bacterial_functional_group(constants: SoilConsts) -> MicrobialGroupConstants:
    """Collect the constants for the bacterial functional group.

    Args:
        constants: The constants for the soil model.

    Returns:
        A
        :class:`~virtual_ecosystem.models.soil.microbial_groups.MicrobialGroupConstants`
        object parameterized with the full set of constants needed to define the
        bacterial functional group.
    """

    return MicrobialGroupConstants(
        max_uptake_rate_labile_C=constants.max_bacterial_uptake_rate_labile_C,
        activation_energy_uptake_rate=constants.activation_energy_microbial_uptake,
        half_sat_labile_C_uptake=constants.half_sat_bacterial_labile_C_uptake,
        activation_energy_uptake_saturation=constants.activation_energy_uptake_saturation,
        max_uptake_rate_ammonium=constants.max_bacterial_uptake_rate_ammonium,
        half_sat_ammonium_uptake=constants.half_sat_bacterial_ammonium_uptake,
        max_uptake_rate_nitrate=constants.max_bacterial_uptake_rate_nitrate,
        half_sat_nitrate_uptake=constants.half_sat_bacterial_nitrate_uptake,
        max_uptake_rate_labile_p=constants.max_bacterial_uptake_rate_labile_p,
        half_sat_labile_p_uptake=constants.half_sat_bacterial_labile_p_uptake,
        turnover_rate=constants.bacterial_turnover_rate,
        activation_energy_turnover=constants.activation_energy_microbial_turnover,
        c_n_ratio=constants.bacterial_c_n_ratio,
        c_p_ratio=constants.bacterial_c_p_ratio,
    )


def make_fungal_functional_group(constants: SoilConsts) -> MicrobialGroupConstants:
    """Collect the constants for the fungal functional group.

    Args:
        constants: The constants for the soil model.

    Returns:
        A
        :class:`~virtual_ecosystem.models.soil.microbial_groups.MicrobialGroupConstants`
        object parameterized with the full set of constants needed to define the fungal
        functional group.
    """

    return MicrobialGroupConstants(
        max_uptake_rate_labile_C=constants.max_fungal_uptake_rate_labile_C,
        activation_energy_uptake_rate=constants.activation_energy_microbial_uptake,
        half_sat_labile_C_uptake=constants.half_sat_fungal_labile_C_uptake,
        activation_energy_uptake_saturation=constants.activation_energy_uptake_saturation,
        max_uptake_rate_ammonium=constants.max_fungal_uptake_rate_ammonium,
        half_sat_ammonium_uptake=constants.half_sat_fungal_ammonium_uptake,
        max_uptake_rate_nitrate=constants.max_fungal_uptake_rate_nitrate,
        half_sat_nitrate_uptake=constants.half_sat_fungal_nitrate_uptake,
        max_uptake_rate_labile_p=constants.max_fungal_uptake_rate_labile_p,
        half_sat_labile_p_uptake=constants.half_sat_fungal_labile_p_uptake,
        turnover_rate=constants.fungal_turnover_rate,
        activation_energy_turnover=constants.activation_energy_microbial_turnover,
        c_n_ratio=constants.fungal_c_n_ratio,
        c_p_ratio=constants.fungal_c_p_ratio,
    )
