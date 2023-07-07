"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_constants` module contains
constants and parameters for the
:mod:`~virtual_rainforest.models.hydrology.hydrology_model`. This is a temporary
solution; we are working on consistent use of constants across all models.

TODO Soil parameters vary strongly with soil type and will require literature search and
sensitivity analysis to produce meaningful results.
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
    "meters_to_millimeters": 1000,
    "celsius_to_kelvin": 273.15,
    "psychrometric_constant": 0.067,  # kPa/C
}
"""Parameters for hydrology model."""
