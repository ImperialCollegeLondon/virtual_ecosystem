"""The :mod:`~virtual_rainforest.models.litter.constants` module contains
constants and parameters for the
:mod:`~virtual_rainforest.models.litter.litter_model`. These parameters are constants
in that they should not be changed during a particular simulation.
"""  # noqa: D205, D415

# TODO - Need to track down better estimates of the carbon use efficiencies.

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class LitterConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `litter` model."""

    litter_decomp_reference_temp: float = 40.0
    """Reference temperature for litter decomposition [C].

    Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_decomp_offset_temp: float = 31.79
    """Offset temperature for litter decomposition [C].

    Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_decomp_temp_response: float = 3.36
    """Parameter controlling the temperature response strength of litter decomposition.

    [unitless]. Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_decay_water_potential_optimum: float = -10.0
    """The water potential at which below ground litter decay is maximised [kPa].

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    litter_decay_water_potential_halt: float = -28800.0
    """The water potential at which below ground litter decay stops entirely [kPa].

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    moisture_response_curvature: float = 1.0
    """Curvature of the litter decay moisture response function [unitless].

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    litter_decay_constant_metabolic_above: float = 0.56 / 7.0
    """Decay constant for the above ground metabolic litter pool [day^-1].

    Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_decay_constant_structural_above: float = 0.152 / 7.0
    """Decay constant for the above ground structural litter pool [day^-1].

    Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_decay_constant_woody: float = 1.0 / 150.0
    """Decay constant for the woody litter pool [day^-1].

    Value is taken from :cite:t:`kirschbaum_modelling_2002` as the average of fine wood
    and coarse wood decay.
    """

    litter_decay_constant_metabolic_below: float = 1.0 / 10.0
    """Decay constant for the below ground metabolic litter pool [day^-1].

    Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_decay_constant_structural_below: float = 1.0 / 37.0
    """Decay constant for the below ground structural litter pool [day^-1].

    Value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    litter_input_to_metabolic_above: float = 0.000280628
    """Litter input rate to metabolic above ground litter pool [kg C m^-2 day^-1].

    This value was estimated (very unsystematically) from SAFE project data. This
    constant will eventually be removed once the litter is linked to other models.
    """

    litter_input_to_structural_above: float = 0.00071869
    """Litter input rate to metabolic above ground litter pool [kg C m^-2 day^-1].

    This value was estimated (very unsystematically) from SAFE project data. This
    constant will eventually be removed once the litter is linked to other models.
    """

    litter_input_to_woody: float = 0.002586
    """Litter input rate to woody litter pool [kg C m^-2 day^-1].

    This was calculated assuming that dead wood pools in old growth forest are at steady
    state. So, that the input will equal the dead wood respiration divided by 1 minus
    the carbon use efficiency. The value for dead wood respiration for old growth forest
    was taken from :cite:t:`mills_tropical_2023`. This constant will eventually be
    removed once the litter is linked to other models.
    """

    litter_input_to_metabolic_below: float = 0.00042
    """Litter input rate to metabolic below ground litter pool [kg C m^-2 day^-1].

    This value was estimated (very unsystematically) from SAFE project data. This
    constant will eventually be removed once the litter is linked to other models.
    """

    litter_input_to_structural_below: float = 0.00048
    """Litter input rate to structural below ground litter pool [kg C m^-2 day^-1].

    This value was estimated (very unsystematically) from SAFE project data. This
    constant will eventually be removed once the litter is linked to other models.
    """

    cue_metabolic: float = 0.45
    """Carbon use efficiency of metabolic litter decay [unitless].

    The value given here is taken from :cite:t:`fatichi_mechanistic_2019`, but I can't
    track down an empirical source. This carbon use efficiency is constant with
    temperature, soil moisture and substrate stoichiometry. These assumptions are not
    made in the soil model, but are used for the sake of simplicity here. If an improved
    version of the litter model gets made, this is a key area to address.
    """

    cue_structural_above_ground: float = 0.55
    """Carbon use efficiency of aboveground structural litter decay [unitless].

    The value given here is taken from :cite:t:`fatichi_mechanistic_2019`; see
    documentation for :attr:`cue_metabolic` for details.
    """

    cue_woody: float = 0.55
    """Carbon use efficiency of woody litter decay [unitless].

    The value given here is taken from :cite:t:`fatichi_mechanistic_2019`; see
    documentation for :attr:`cue_metabolic` for details.
    """

    cue_structural_below_ground: float = 0.45
    """Carbon use efficiency of belowground structural litter decay [unitless].

    The value given here is taken from :cite:t:`fatichi_mechanistic_2019`; see
    documentation for :attr:`cue_metabolic` for details.
    """

    depth_of_active_layer: float = 0.25
    """Depth of the biogeochemically active soil layer [m].

    The soil model considered a homogenous layer in which all significant nutrient
    processes take place. This is a major assumption of the model. The value is taken
    from :cite:t:`fatichi_mechanistic_2019`. No empirical source is provided for this
    value.

    This is really a core constant as it is shared across models. However, the core
    constants are not yet setup, so this constant is being stored here for the time
    being.
    """

    lignin_inhibition_factor: float = -5.0
    """Exponential factor expressing the extent that lignin inhibits litter breakdown.

    [unitless]. The more negative this value the greater the strength of the inhibition.
    This value is taken from :cite:t:`kirschbaum_modelling_2002`.
    """

    lignin_proportion_above_structural_input: float = 0.25
    """Lignin proportion of input to the above ground structural litter pool [unitless].

    TODO - The number given here is made up (but within reasonable bounds). However,
    this is a quantity that should be generated by the plant model.
    """

    lignin_proportion_wood_input: float = 0.3
    """Lignin proportion of dead wood input [unitless].

    TODO - The number given here is made up (but within reasonable bounds). However,
    this is a quantity that should be generated by the plant model.
    """

    lignin_proportion_below_structural_input: float = 0.2
    """Lignin proportion of input to the below ground structural litter pool [unitless].

    TODO - The number given here is made up (but within reasonable bounds). However,
    this is a quantity that should be generated by the plant model.
    """
