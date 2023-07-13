"""The ``models.abiotic_simple.constants`` module contains a set of dataclasses
containing parameters  required by the broader
:mod:`~virtual_rainforest.models.abiotic_simple` model. These parameters are constants
in that they should not be changed during a particular simulation.
"""  # noqa: D205, D415

MicroclimateGradients: dict[str, float] = {
    "air_temperature_gradient": -1.27,
    "relative_humidity_gradient": 5.4,
    "vapour_pressure_deficit_gradient": -252.24,
}
"""Gradients for linear regression to calculate air temperature, relative humidity, and
vapour pressure deficit as a function of leaf area index from
:cite:t:`hardwick_relationship_2015`.
"""

MicroclimateParameters: dict[str, float] = {
    "saturation_vapour_pressure_factor1": 0.61078,
    "saturation_vapour_pressure_factor2": 7.5,
    "saturation_vapour_pressure_factor3": 237.3,
}
"""Parameters for simple abiotic regression model."""
