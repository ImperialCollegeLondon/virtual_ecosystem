"""Dummy data set to mimic Data.data object."""


from typing import Any, Dict

data: Dict[str, Any] = {
    "soil_depth": 2.0,  # meter, might not change
    "time_1": {
        "air_temperature_2m": 25,  # Celsius
        "relative_humidity_2m": 90,  # percent
        "atmospheric_pressure_2m": 101.325,  # kPa
        "wind_speed_10m": 2.0,  # m s-1
        "soil_moisture_reference": 0.3,  # fraction
        "mean_annual_temperature": 20.0,  # Celsius
    },
    "time_2": {
        "air_temperature_2m": 25,  # Celsius
        "relative_humidity_2m": 90,  # percent
        "atmospheric_pressure_2m": 101.325,  # kPa
        "wind_speed_10m": 2.0,  # m s-1
        "soil_moisture_reference": 0.3,  # fraction
        "mean_annual_temperature": 20.0,  # Celsius, might not change
    },
}

# soil parameter for different soil types, no real values, will be external data base
soil_parameters: Dict[str, Any] = {  # these are not real values
    "Sand": {
        "Smax": 1,  # Volumetric water content at saturation (m^3 / m^3)
        "Smin": 1,  # Residual water content (m^3 / m^3)
        "alpha": 1,  # Shape parameter of the van Genuchten model (cm^-1)
        "n": 1,  # Pore_size_distribution_parameter (dimensionless, > 1)
        "Ksat": 1,  # Saturated hydraulic conductivity (cm / day)
        "Vq": 1,  # Volumetric quartz content of soil
        "Vm": 1,  # Volumetric mineral content of soil
        "Vo": 1,  # Volumetric organic content of soil
        "Mc": 1,  # Mass fraction of clay
        "rho": 1,  # Soil bulk density (Mg / m^3)
        "b": 1,  # Shape parameter for Campbell model (dimensionless, > 1)
        "psi_e": 1,  # Matric potential (J / m^3)
    },
    "Clay": {
        "Smax": 1,  # Volumetric water content at saturation (m^3 / m^3)
        "Smin": 1,  # Residual water content (m^3 / m^3)
        "alpha": 1,  # Shape parameter of the van Genuchten model (cm^-1)
        "n": 1,  # Pore_size_distribution_parameter (dimensionless, > 1)
        "Ksat": 1,  # Saturated hydraulic conductivity (cm / day)
        "Vq": 1,  # Volumetric quartz content of soil
        "Vm": 1,  # Volumetric mineral content of soil
        "Vo": 1,  # Volumetric organic content of soil
        "Mc": 1,  # Mass fraction of clay
        "rho": 1,  # Soil bulk density (Mg / m^3)
        "b": 1,  # Shape parameter for Campbell model (dimensionless, > 1)
        "psi_e": 1,  # Matric potential (J / m^3)
    },
}
