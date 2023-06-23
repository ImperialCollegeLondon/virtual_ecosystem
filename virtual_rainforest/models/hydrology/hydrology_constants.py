"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_constants` module contains
constants and parameters for the hydrology model. This is a temporary solution.
"""  # noqa: D205, D415

from typing import Dict

HydrologyParameters: Dict[str, float] = {
    "soil_moisture_capacity": 0.9,  # dimensionless
    "water_interception_factor": 0.1,  # dimensionless
    "hydraulic_conductivity": 0.001,  # m/s
    "hydraulic_gradient": 0.01,  # m/m
    "seconds_to_month": 2.628e6,
    "alpha": 0.01,
    "nonlinearily_parameter": 2.0,
}
"""Parameters for hydrology model."""

# TODO move bounds to core.bound_checking once that is implemented and introduce method
# to conserve energy and matter
