"""The :mod:`~virtual_rainforest.models.hydrology.constants` module contains
constants and parameters for the
:mod:`~virtual_rainforest.models.hydrology.hydrology_model`. This is a temporary
solution; we are working on consistent use of constants across all models.

TODO Soil parameters vary strongly with soil type and will require literature search and
sensitivity analysis to produce meaningful results.
"""  # noqa: D205, D415


HydroConsts: dict[str, float] = {
    "soil_moisture_capacity": 0.9,  # dimensionless
    "soil_moisture_residual": 0.1,  # dimensionless
    "water_interception_factor": 0.1,  # dimensionless
    "hydraulic_conductivity": 0.001,  # m/s
    "hydraulic_gradient": 0.01,  # m/m
    "seconds_to_month": 2.628e6,
    "nonlinearily_parameter": 2.0,
    "meters_to_millimeters": 1000,
    "celsius_to_kelvin": 273.15,
    "density_air": 1.225,  # kg m-3
    "latent_heat_vapourisation": 2.45,  # MJ kg-1
    "gas_constant_water_vapour": 461.51,  # J kg-1 K-1
    "heat_transfer_coefficient": 12.5,  # `van_de_griend_bare_1994`
    "flux_to_mm_conversion": 3.35e-4,
}
"""Constants for hydrology model."""
