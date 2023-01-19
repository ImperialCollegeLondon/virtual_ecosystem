"""Dummy file to mimik core.constants."""

LEAF_TEMPERATURE_INI_FACTOR = 0.01
"""factor used to initialise leaf temperature"""
SOIL_DIVISION_FACTOR = 2.42
"""factor defines how to divide soil into layers with increasing thickness, alternative
value 1.2"""
MIN_LEAF_CONDUCTIVITY = 0.25
"""min leaf conductivity, typical for decidious forest with wind above canopy 2 m/s"""
MAX_LEAF_CONDUCTIVITY = 0.32
"""max leaf conductivity, typical for decidious forest with wind above canopy 2 m/s"""
AIR_CONDUCTIVITY = 50.0
"""initial air conductivity, typical for decid. forest with wind above canopy 2 m/s"""
MIN_LEAF_AIR_CONDUCTIVITY = 0.13
"""min conductivity between leaf and air, typical for decidious forest with wind above
canopy 2 m/s"""
MAX_LEAF_AIR_CONDUCTIVITY = 0.19
"""max conductivity between leaf and air, typical for decidious forest with wind above
canopy 2 m/s"""
KARMANS_CONSTANT = 0.4
"""constant to calculate mixing length"""
CELSIUS_TO_KELVIN = 273.15
"""factor to convert temperature in Celsius to absolute temperature in Kelvin"""
STANDARD_MOLE = 44.6
"""moles of ideal gas in 1 m3 air at standard atmosphere"""
MOLAR_HEAT_CAPACITY_AIR = 29.19
"""molar heat capacity of air [J mol-1 C-1]"""
VAPOR_PRESSURE_FACTOR1 = 0.6108
"""constant in calculation of vapor pressure"""
VAPOR_PRESSURE_FACTOR2 = 17.27
"""constant in calculation of vapor pressure"""
VAPOR_PRESSURE_FACTOR3 = 237.7
"""constant in calculation of vapor pressure"""
LIGHT_EXCTINCTION_COEFFICIENT = 0.01
"""light extinction coefficient for canopy"""
