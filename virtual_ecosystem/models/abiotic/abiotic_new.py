"""This is a python version of the micropoint package my Maclean, translated from C++.

Todo:
- check variable names are interpreted correctly
- move constants and parameters to separate constants file
- some functions need more spliting up and unit testing
- test the functions against original
- integrate in flow
- adjust for numpy arrays in all dimensions
- add horizontal dimension
- check what can be replaced by pyrealm
- check where top and bottom is, I think microclims starts near surface
"""

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.logger import LOGGER


def calculate_julian_day(year: int, month: int, day: int) -> int:
    """Calculate Astronomical Julian day.

    Can be replaced by pyrealm version when available.

    Args:
        year: Year
        month: Month
        day: Day

    Returns:
        Julian day
    """
    day_adjusted = day + 0.5
    month_adjusted = month + (month < 3) * 12
    year_adjusted = year + (month < 3) * -1
    julian = (
        np.trunc(365.25 * (year_adjusted + 4716))
        + np.trunc(30.6001 * (month_adjusted + 1))
        + day_adjusted
        - 1524.5
    )
    correction_factor = (
        2 - np.trunc(year_adjusted / 100) + np.trunc(np.trunc(year_adjusted / 100) / 4)
    )
    julian_day = int(julian + (julian > 2299160) * correction_factor)
    return julian_day


def calculate_solar_time(
    julian_day: int, local_time: float, longitude: NDArray[np.float64]
) -> float:
    """Calculate solar time.

    Args:
        julian_day: Julian day, e.g. for September 4, 2023 julian_day=2460192
        local_time: Local time, e.g. noon local_time=12.0
        longitude: Longitude, decimal degrees

    Returns:
        solar time
    """
    # Calculate the mean anomaly of the Sun
    mean_anomaly = 6.24004077 + 0.01720197 * (julian_day - 2451545)

    # Calculate the equation of time (EoT)
    equation_of_time = -7.659 * np.sin(mean_anomaly) + 9.863 * np.sin(
        2 * mean_anomaly + 3.5932
    )

    # Calculate the solar time
    solar_time = local_time + (4 * longitude + equation_of_time) / 60

    return solar_time


def calculate_solar_position(
    latitude: NDArray[np.float64],
    longitude: NDArray[np.float64],
    year: int,
    month: int,
    day: int,
    local_time: float,
) -> list[NDArray[np.float64]]:
    """Calculate solar position.

    Args:
        latitude: Latitude, decimal degrees
        longitude: Longitude, decimal degrees
        year: Year
        month: Month
        day: Day
        local_time: Local time

    Returns:
        solar zenith angle and solar azimuth angle in degree
    """
    # Calculate Julian day and solar time
    julian_day = calculate_julian_day(year=year, month=month, day=day)
    solar_time = calculate_solar_time(
        julian_day=julian_day, local_time=local_time, longitude=longitude
    )

    # Convert latitude to radians
    latitude_rad = np.radians(latitude)

    # Calculate solar declination
    solar_declination = np.radians(23.5) * np.cos(
        (2 * np.pi * julian_day - 159.5) / 365.25
    )

    # Calculate Solar hour angle
    solar_hour_angle = np.radians(0.261799 * (solar_time - 12))

    # Calculate solar zenith angle
    coh = np.sin(solar_declination) * np.sin(latitude_rad) + np.cos(
        solar_declination
    ) * np.cos(latitude_rad) * np.cos(solar_hour_angle)
    solar_zenith_angle = np.degrees(np.acos(coh))

    # Calculate solar azimuth angle
    sh = np.sin(solar_declination) * np.sin(latitude_rad) + np.cos(
        solar_declination
    ) * np.cos(latitude_rad) * np.cos(solar_hour_angle)
    hh = np.atan(sh / np.sqrt(1 - sh * sh))
    sazi = np.cos(solar_declination) * np.sin(solar_hour_angle) / np.cos(hh)
    cazi = (
        np.sin(latitude_rad) * np.cos(solar_declination) * np.cos(solar_hour_angle)
        - np.cos(latitude_rad) * np.sin(solar_declination)
    ) / np.sqrt(
        np.pow(np.cos(solar_declination) * np.sin(solar_hour_angle), 2)
        + np.pow(
            np.sin(latitude_rad) * np.cos(solar_declination) * np.cos(solar_hour_angle)
            - np.cos(latitude_rad) * np.sin(solar_declination),
            2,
        )
    )

    sqt = np.maximum(1 - sazi**2, 0)

    solar_azimuth_angle = 180 + (180 * np.atan(sazi / np.sqrt(sqt))) / np.pi

    solar_azimuth_angle = np.where(
        cazi < 0,
        np.where(sazi < 0, 180 - solar_azimuth_angle, 540 - solar_azimuth_angle),
        solar_azimuth_angle,
    )

    return [solar_zenith_angle, solar_azimuth_angle]


def calculate_solar_index(
    slope: NDArray[np.float64],
    aspect: NDArray[np.float64],
    zenith: NDArray[np.float64],
    azimuth: NDArray[np.float64],
    shadowmask=bool,
) -> NDArray[np.float64]:
    """Calculate the solar index.

    Parameters:
        slope: The slope angle in decimal degrees from horizontal
        aspect: The aspect angle in decimal degrees from horizontal
        zenith: The solar zenith angle in decimal degrees
        azimuth: The solar azimuth angle in decimal degrees
        shadowmask: If True, the index is set to 0 if the zenith angle is greater than
            90 degrees

    Returns:
        The solar index
    """

    if not shadowmask:
        zenith = np.where(zenith > 90.0, 0.0, zenith)

    zenith_rad = np.radians(zenith)
    slope_rad = np.radians(slope)
    azimuth_minus_aspect_rad = np.radians(azimuth - aspect)

    # Check for slope == 0.0 element-wise
    solar_index_value = np.where(
        slope == 0.0,
        np.cos(zenith_rad),  # If slope is 0, use cos(zenith_rad)
        (
            np.cos(zenith_rad) * np.cos(slope_rad)
            + np.sin(zenith_rad) * np.sin(slope_rad) * np.cos(azimuth_minus_aspect_rad)
        ),
    )

    return np.maximum(solar_index_value, 0.0)


def calculate_clear_sky_radiation(
    solar_zenith_angle: NDArray[np.float64],
    temperature: NDArray[np.float64],
    relative_humidity: NDArray[np.float64],
    atmospheric_pressure: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate the clear sky radiation for a given set of dates and locations.

    Parameters:
        solar_zenith_angle: Solar zenith angle in degree
        temperature: Temperature, [C]
        relative_humidity: Relative humidity in percent
        atmospheric_pressure: Atmospheric pressures, [hPa]

    Returns:
        List of clear sky radiation values
    """

    solar_zenith_angle_rad = np.radians(solar_zenith_angle)

    # Vectorized condition: apply formula only where solar_zenith_angle <= 90
    optical_thickness = np.where(
        solar_zenith_angle <= 90.0,
        35
        * np.cos(solar_zenith_angle_rad)
        * (1224 * np.cos(solar_zenith_angle_rad) ** 2 + 1) ** -0.5,
        0.0,  # Set to 0 where condition is false
    )

    transmittance_to_zenith = np.where(
        solar_zenith_angle <= 90.0,
        1.021
        - 0.084 * np.sqrt(optical_thickness * 0.00949 * atmospheric_pressure + 0.051),
        0.0,
    )

    log_relative_humidity = np.log(relative_humidity / 100)
    temperature_factor = (17.27 * temperature) / (237.3 + temperature)
    dew_point_temperature = (237.3 * (log_relative_humidity + temperature_factor)) / (
        17.27 - (log_relative_humidity + temperature_factor)
    )

    humidity_adjustment_factor = np.exp(
        0.1133 - np.log(3.78) + 0.0393 * dew_point_temperature
    )

    water_vapor_adjustment = np.where(
        solar_zenith_angle <= 90.0,
        1 - 0.077 * (humidity_adjustment_factor * optical_thickness) ** 0.3,
        0.0,
    )

    aerosol_optical_depth = np.where(
        solar_zenith_angle <= 90.0, 0.935 * optical_thickness, 0.0
    )

    clear_sky_optical_depth = (
        transmittance_to_zenith * water_vapor_adjustment * aerosol_optical_depth
    )

    clear_sky_radiation = np.where(
        solar_zenith_angle <= 90.0,
        1352.778 * np.cos(solar_zenith_angle_rad) * clear_sky_optical_depth,
        0.0,
    )

    return clear_sky_radiation


def calculate_canopy_extinction_coefficients(
    solar_zenith_angle: NDArray[np.float64],
    leaf_inclination_angle_coefficient: float,
    solar_index: NDArray[np.float64],
) -> list[float | NDArray[np.float64]]:
    """Calculate the canopy extinction coefficients for sloped ground surfaces.

    Parameters:
        solar_zenith_angle: Solar zenith angle in degrees
        leaf_inclination_angle_coefficient: Leaf inclination angle coefficient
        solar_index: Solar index value

    Returns:
        List of canopy extinction coefficients [k, kd, k0]
    """
    # Ensure solar zenith angles don't exceed 90 degrees
    solar_zenith_angle = np.where(solar_zenith_angle > 90.0, 90.0, solar_zenith_angle)
    zenith_angle_rad = np.radians(solar_zenith_angle)

    # Calculate normal canopy extinction coefficient k
    if leaf_inclination_angle_coefficient == 1.0:
        extinction_coefficient_k = 1 / (2 * np.cos(zenith_angle_rad))
    elif np.isinf(leaf_inclination_angle_coefficient):
        extinction_coefficient_k = 1.0
    else:
        extinction_coefficient_k = np.sqrt(
            leaf_inclination_angle_coefficient**2 + np.tan(zenith_angle_rad) ** 2
        ) / (
            leaf_inclination_angle_coefficient
            + 1.774 * (leaf_inclination_angle_coefficient + 1.182) ** -0.733
        )

    # Cap extinction coefficient k at 6000
    extinction_coefficient_k = np.where(
        extinction_coefficient_k > 6000.0, 6000.0, extinction_coefficient_k
    )

    # Calculate adjusted k0
    if leaf_inclination_angle_coefficient == 1.0:
        extinction_coefficient_k0 = 0.5
    elif np.isinf(leaf_inclination_angle_coefficient):
        extinction_coefficient_k0 = 1.0
    else:
        extinction_coefficient_k0 = np.sqrt(leaf_inclination_angle_coefficient**2) / (
            leaf_inclination_angle_coefficient
            + 1.774 * (leaf_inclination_angle_coefficient + 1.182) ** -0.733
        )

    # Calculate kd (adjusted extinction coefficient)
    extinction_coefficient_kd = np.where(
        solar_index == 0,
        1.0,
        extinction_coefficient_k * np.cos(zenith_angle_rad) / solar_index,
    )

    return [
        extinction_coefficient_k,  # k
        extinction_coefficient_kd,  # kd
        extinction_coefficient_k0,  # k0
    ]


def calculate_diffuse_radiation_parameters(
    adjusted_plant_area_index: NDArray[np.float64],
    scatter_absorption_coefficient: float,
    backward_scattering_coefficient: float,
    diffuse_scattering_coefficient: float,
    ground_reflectance: float,  # gref
) -> list[float]:
    """Calculates parameters for diffuse radiation using two-stream model.

    Args:
        adjusted_plant_area_index: Plant area index adjusted by clumping factor,
            [m2 m-2]  # reference: pait, with(vegp,(pai/(1-clump)))
        scatter_absorption_coefficient: Absorption coefficient for incoming diffuse
            radiation per unit leaf area   # reference: a, a<-1-om
        backward_scattering_coefficient: Backward scattering coefficient  # reference:
            gma, gma<-0.5*(om+J*del)
        diffuse_scattering_coefficient: Constant diffuse radiation related coefficient
          # reference: , h<-sqrt(a^2+2*a*gma)
        ground_reflectance: Ground reflectance (0-1)

    Returns:
        List of diffuse radiation parameters [p1, p2, p3, p4]
    """

    # Handle division by zero for ground reflectance
    if ground_reflectance == 0:
        ground_reflectance = np.finfo(np.float64).eps

    # Calculate base parameters
    leaf_extinction_factor = np.exp(
        -diffuse_scattering_coefficient * adjusted_plant_area_index
    )
    u1 = scatter_absorption_coefficient + backward_scattering_coefficient * (
        1 - 1 / ground_reflectance
    )
    u2 = scatter_absorption_coefficient + backward_scattering_coefficient * (
        1 - ground_reflectance
    )
    d1 = (
        scatter_absorption_coefficient
        + backward_scattering_coefficient
        + diffuse_scattering_coefficient
    ) * (u1 - diffuse_scattering_coefficient) * 1 / leaf_extinction_factor - (
        scatter_absorption_coefficient
        + backward_scattering_coefficient
        - diffuse_scattering_coefficient
    ) * (u1 + diffuse_scattering_coefficient) * leaf_extinction_factor
    d2 = (u2 + diffuse_scattering_coefficient) * 1 / leaf_extinction_factor - (
        u2 - diffuse_scattering_coefficient
    ) * leaf_extinction_factor

    # Calculate parameters
    parameter_1 = (backward_scattering_coefficient / (d1 * leaf_extinction_factor)) * (
        u1 - diffuse_scattering_coefficient
    )
    parameter_2 = (-backward_scattering_coefficient * leaf_extinction_factor / d1) * (
        u1 + diffuse_scattering_coefficient
    )
    parameter_3 = (1 / (d2 * leaf_extinction_factor)) * (
        u2 + diffuse_scattering_coefficient
    )
    parameter_4 = (-leaf_extinction_factor / d2) * (u2 - diffuse_scattering_coefficient)

    return [parameter_1, parameter_2, parameter_3, parameter_4]


def calculate_direct_radiation_parameters(
    adjusted_plant_area_index: NDArray[np.float64],
    scattering_albedo: float,
    scatter_absorption_coefficient: float,
    backward_scattering_coefficient: float,
    diffuse_scattering_coefficient: float,
    ground_reflectance: float,
    inclination_distribution: float,
    delta_reflectance_transmittance: float,
    extinction_coefficient_k: NDArray[np.float64],
    extinction_coefficient_kd: NDArray[np.float64],
    sigma: float,
) -> list[float]:
    """Calculates parameters for direct radiation using two-stream model.

    TODO this needs to be more readable and with more unit tests.

    Args:
        adjusted_plant_area_index: Plant area index adjusted by clumping factor
            # reference: pait, with(vegp,(pai/(1-clump)))
        scattering_albedo: Single scattering albedo of individual canopy elements
            # reference: om, om<-with(vegp,lref+ltra)
        scatter_absorption_coefficient: Absorption coefficient for incoming diffuse
            radiation per unit leaf area  # reference: a, a<-1-om
        backward_scattering_coefficient: Backward scattering coefficient  # reference:
            gma, gma<-0.5*(om+J*del)
        diffuse_scattering_coefficient: Constant diffuse radiation related coefficient
          # reference: , h<-sqrt(a^2+2*a*gma)
        ground_reflectance: Ground reflectance (0-1)
        inclination_distribution: Integral function of the inclination distribution of
            canopy elements
        delta_reflectance_transmittance: Difference between canopy element reflectance
            and canopy element transmittance
        extinction_coefficient_k: Normal canopy extinction coefficient
        extinction_coefficient_kd: Adjusted canopy extinction coefficient
        sigma: sigma

    Returns:
        List of direct radiation parameters [parameter_5 to parameter_10]
    """

    # Calculate base parameters
    ss = (
        0.5
        * (
            scattering_albedo
            + inclination_distribution
            * delta_reflectance_transmittance
            / extinction_coefficient_k
        )
        * extinction_coefficient_k
    )
    sstr = scattering_albedo * extinction_coefficient_k - ss

    # Calculate intermediate parameters
    leaf_extinction_factor_1 = np.exp(
        -diffuse_scattering_coefficient * adjusted_plant_area_index
    )
    leaf_extinction_factor_2 = np.exp(
        -extinction_coefficient_kd * adjusted_plant_area_index
    )

    # Calculate parameters
    u1 = scatter_absorption_coefficient + backward_scattering_coefficient * (
        1 - 1 / ground_reflectance
    )
    u2 = scatter_absorption_coefficient + backward_scattering_coefficient * (
        1 - ground_reflectance
    )
    d1 = (
        scatter_absorption_coefficient
        + backward_scattering_coefficient
        + diffuse_scattering_coefficient
    ) * (u1 - diffuse_scattering_coefficient) * 1 / leaf_extinction_factor_1 - (
        scatter_absorption_coefficient
        + backward_scattering_coefficient
        - diffuse_scattering_coefficient
    ) * (u1 + diffuse_scattering_coefficient) * leaf_extinction_factor_1
    d2 = (u2 + diffuse_scattering_coefficient) * 1 / leaf_extinction_factor_1 - (
        u2 - diffuse_scattering_coefficient
    ) * leaf_extinction_factor_1
    parameter_5 = (
        -ss
        * (
            scatter_absorption_coefficient
            + backward_scattering_coefficient
            - extinction_coefficient_kd
        )
        - backward_scattering_coefficient * sstr
    )
    v1 = (
        ss
        - (
            parameter_5
            * (
                scatter_absorption_coefficient
                + backward_scattering_coefficient
                + extinction_coefficient_kd
            )
        )
        / sigma
    )
    v2 = (
        ss
        - backward_scattering_coefficient
        - (parameter_5 / sigma) * (u1 + extinction_coefficient_kd)
    )
    parameter_6 = (1 / d1) * (
        (v1 / leaf_extinction_factor_1) * (u1 - diffuse_scattering_coefficient)
        - (
            scatter_absorption_coefficient
            + backward_scattering_coefficient
            - diffuse_scattering_coefficient
        )
        * leaf_extinction_factor_2
        * v2
    )
    parameter_7 = (-1 / d1) * (
        (v1 * leaf_extinction_factor_1) * (u1 + diffuse_scattering_coefficient)
        - (
            scatter_absorption_coefficient
            + backward_scattering_coefficient
            + diffuse_scattering_coefficient
        )
        * leaf_extinction_factor_2
        * v2
    )
    parameter_8 = (
        sstr
        * (
            scatter_absorption_coefficient
            + backward_scattering_coefficient
            + extinction_coefficient_kd
        )
        - backward_scattering_coefficient * ss
    )
    v3 = (
        sstr
        + backward_scattering_coefficient * ground_reflectance
        - (parameter_8 / sigma) * (u2 - extinction_coefficient_kd)
    ) * leaf_extinction_factor_2
    parameter_9 = (-1 / d2) * (
        (parameter_8 / (sigma * leaf_extinction_factor_1))
        * (u2 + diffuse_scattering_coefficient)
        + v3
    )
    parameter_10 = (1 / d2) * (
        ((parameter_8 * leaf_extinction_factor_1) / sigma)
        * (u2 - diffuse_scattering_coefficient)
        + v3
    )

    return [
        parameter_5,
        parameter_6,
        parameter_7,
        parameter_8,
        parameter_9,
        parameter_10,
    ]


def calculate_absorbed_shortwave_radiation(
    plant_area_index: NDArray[np.float64],
    leaf_orientation_coefficient: NDArray[np.float64],
    leaf_reluctance_shortwave: float,
    leaf_transmittance_shortwave: float,
    clumping_factor: float,
    ground_reflectance: float,
    slope: NDArray[np.float64],
    aspect: NDArray[np.float64],
    latitude: NDArray[np.float64],
    longitude: NDArray[np.float64],
    year: int,
    month: int,
    day: int,
    local_time: float,
    shortwave_radiation: NDArray[np.float64],
    diffuse_radiation: NDArray[np.float64],
    leaf_inclination_angle_coefficient: float,
) -> dict[str, NDArray[np.float64]]:
    """Calculate absorbed shortwave radiation for ground and canopy.

    The initial model is for a time series and includes a loop, here only for one time
    step. The ground absorption as an additional dimension, needs fixing.

    Args:
        plant_area_index: Plant area index, [m2 m-2]?
        leaf_orientation_coefficient: Coefficient that represents how vertically or
            horizontally the leaves of the canopy are orientated and controls how much
            direct radiation is transmitted through the canopy at a given solar angle
            (when the sun is low above the horizon, less radiation is transmitted
            through vertically orientated leaves)
        leaf_reluctance_shortwave: Leaf reluctance of shortwave radiation (0-1)
        leaf_transmittance_shortwave: Leaf transmittance od shortwave radiation (0-1)
        clumping_factor: Canopy clumping factor
        ground_reflectance: Ground reflectance (0-1)
        slope: Slope of the ground surface (decimal degrees from horizontal)
        aspect: Aspect of the ground surface (decimal degrees from north)
        latitude: Latitude in decimal degree
        longitude: Longitude in decimal degree
        year: Year
        month: Month
        day: Day
        local_time: Local time
        shortwave_radiation: Shortwave radiation, [W m-2]
        diffuse_radiation: Diffuse radiation, [W m-2]
        leaf_inclination_angle_coefficient: Leaf inclination angle coefficient

    Returns:
        dictionary with ground and canopy absorbed radiation
    """

    # Initialize output variables
    output = {}

    # Calculate time-invariant variables
    adjusted_plant_area_index = plant_area_index / (1 - clumping_factor)

    scattering_albedo = leaf_reluctance_shortwave + leaf_transmittance_shortwave
    scatter_absorption_coefficient = 1 - scattering_albedo
    delta_reflectance_transmittance = (
        leaf_reluctance_shortwave - leaf_transmittance_shortwave
    )

    # Calculate mean_inclination_angle where leaf orientation coefficient is not = 1.0
    mean_inclination_angle_full = np.where(
        leaf_orientation_coefficient != 1.0,
        9.65 * np.power((3 + leaf_orientation_coefficient), -1.65),
        1.0 / 3.0,  # note: value from micropoint
    )

    # Clip mean_inclination_angle values to be at most π/2
    mean_inclination_angle = np.minimum(mean_inclination_angle_full, np.pi / 2)

    # Calculate inclination distribution
    inclination_distribution = np.cos(mean_inclination_angle) ** 2

    backward_scattering_coefficient = 0.5 * (
        scattering_albedo + inclination_distribution * delta_reflectance_transmittance
    )
    diffuse_scattering_coefficient = np.sqrt(
        scatter_absorption_coefficient**2
        + 2 * scatter_absorption_coefficient * backward_scattering_coefficient
    )

    # Calculate two-stream parameters (diffuse)
    diffuse_radiation_parameters = calculate_diffuse_radiation_parameters(
        adjusted_plant_area_index=adjusted_plant_area_index,
        scatter_absorption_coefficient=scatter_absorption_coefficient,
        backward_scattering_coefficient=backward_scattering_coefficient,
        diffuse_scattering_coefficient=diffuse_scattering_coefficient,
        ground_reflectance=ground_reflectance,
    )
    p1, p2, p3, p4 = diffuse_radiation_parameters

    # Downward diffuse stream
    clumping_factor_diffuse = clumping_factor**2
    diffuse_downward_radiation_full = (
        (1 - clumping_factor_diffuse)
        * (
            p3 * np.exp(-diffuse_scattering_coefficient * adjusted_plant_area_index)
            + p4 * np.exp(diffuse_scattering_coefficient * adjusted_plant_area_index)
        )
        + clumping_factor_diffuse,
    )
    diffuse_downward_radiation = np.minimum(diffuse_downward_radiation_full, 1.0)

    # Calculate two-stream parameters (direct)
    # Calculate solar variables
    solar_position = calculate_solar_position(
        latitude=latitude,
        longitude=longitude,
        year=year,
        month=month,
        day=day,
        local_time=local_time,
    )
    zenith, azimuth = solar_position
    solar_index = calculate_solar_index(
        slope=slope,
        aspect=aspect,
        zenith=zenith,
        azimuth=azimuth,
    )
    zenith = np.minimum(zenith, 90.0)

    # Calculate canopy extinction coefficients
    canopy_extinction_coefficients = calculate_canopy_extinction_coefficients(
        solar_zenith_angle=zenith,
        leaf_inclination_angle_coefficient=leaf_inclination_angle_coefficient,
        solar_index=solar_index,
    )
    k, kd, k0 = canopy_extinction_coefficients
    kc = kd / k0

    # Calculate two-stream parameters (direct)
    sigma = (
        kd**2
        + backward_scattering_coefficient**2
        - (scatter_absorption_coefficient + backward_scattering_coefficient) ** 2
    )

    direct_radiation_parameters = calculate_direct_radiation_parameters(
        adjusted_plant_area_index=adjusted_plant_area_index,
        scattering_albedo=scattering_albedo,
        scatter_absorption_coefficient=scatter_absorption_coefficient,
        backward_scattering_coefficient=backward_scattering_coefficient,
        inclination_distribution=inclination_distribution,
        delta_reflectance_transmittance=delta_reflectance_transmittance,
        diffuse_scattering_coefficient=diffuse_scattering_coefficient,
        ground_reflectance=ground_reflectance,
        extinction_coefficient_k=k,
        extinction_coefficient_kd=kd,
        sigma=sigma,
    )
    p5, p6, p7, p8, p9, p10 = direct_radiation_parameters

    # Calculate albedo
    albedo_diffuse = (1 - clumping_factor_diffuse) * (
        p1 + p2
    ) + clumping_factor_diffuse * ground_reflectance
    clumping_factor_beam = clumping_factor**kc
    albedo_beam = (1 - clumping_factor_beam) * (
        p5 / sigma + p6 + p7
    ) + clumping_factor_beam * ground_reflectance
    albedo_beam = np.where(np.isinf(albedo_beam), albedo_diffuse, albedo_beam)

    beam_radiation = (shortwave_radiation - diffuse_radiation) / np.cos(
        zenith * np.pi / 180
    )
    # Contribution of direct to downward diffuse stream
    diffuse_beam_radiation = (1 - clumping_factor_beam) * (
        (p8 / sigma) * np.exp(-kd * adjusted_plant_area_index)
        + p9 * np.exp(-diffuse_scattering_coefficient * adjusted_plant_area_index)
        + p10 * np.exp(diffuse_scattering_coefficient * adjusted_plant_area_index)
    )
    diffuse_beam_radiation = np.clip(diffuse_beam_radiation, 0.0, 1.0)

    # Downward direct stream
    downward_direct_stream = (1 - clumping_factor_beam) * np.exp(
        -kd * adjusted_plant_area_index
    ) + clumping_factor_beam
    downward_direct_stream = np.minimum(downward_direct_stream, 1)

    # Radiation absorbed by ground
    diffuse_radiation_ground = (1 - ground_reflectance) * (
        diffuse_beam_radiation * beam_radiation
        + diffuse_downward_radiation * diffuse_radiation
    )
    direct_radiation_ground = (1 - ground_reflectance) * (
        downward_direct_stream * beam_radiation * solar_index
    )

    ground_shortwave_absorption_veg = diffuse_radiation_ground + direct_radiation_ground

    # Radiation absorbed by canopy TODO coordinate with plants model
    diffuse_radiation_canopy = (1 - albedo_diffuse) * diffuse_radiation
    direct_radiation_canopy = (1 - albedo_beam) * beam_radiation * solar_index
    canopy_shortwave_absorption_veg = diffuse_radiation_canopy + direct_radiation_canopy

    albedo_veg = np.clip(
        1 - (canopy_shortwave_absorption_veg / shortwave_radiation), 0.01, 0.99
    )

    # where plant area index not >0
    ground_shortwave_absorption_no_veg = (1 - ground_reflectance) * (
        diffuse_radiation + solar_index * beam_radiation
    )

    ground_shortwave_absorption = np.where(
        plant_area_index > 0,
        ground_shortwave_absorption_veg,
        ground_shortwave_absorption_no_veg,
    )
    canopy_shortwave_absorption = np.where(
        plant_area_index > 0,
        canopy_shortwave_absorption_veg,
        ground_shortwave_absorption_no_veg,
    )
    albedo = np.where(plant_area_index > 0, albedo_veg, ground_reflectance)

    # return values for positive shortwave radiation, else 0.
    output["ground_shortwave_absorption"] = np.where(
        shortwave_radiation > 0,
        ground_shortwave_absorption,
        0.0,
    ).squeeze()  # TODO for some reason I have extra dimension here
    output["canopy_shortwave_absorption"] = np.where(
        shortwave_radiation > 0,
        canopy_shortwave_absorption,
        0.0,
    )

    output["albedo"] = np.where(
        shortwave_radiation > 0, albedo, leaf_reluctance_shortwave
    )

    return output


def calculate_molar_density_air(
    temperature: NDArray[np.float64],
    atmospheric_pressure: NDArray[np.float64],
    standard_mole: float,
    standard_pressure: float,
    celsius_to_kelvin: float,
) -> NDArray[np.float64]:
    """Calculate temperature-dependent molar density of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: Air temperature, [C]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        standard_mole: Moles of ideal gas in 1 m^3 air at standard atmosphere
        standard_pressure: Standard atmospheric pressure, [kPa]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin

    Returns:
        molar density of air, [mol m-3]
    """

    temperature_kelvin = temperature + celsius_to_kelvin

    return (
        standard_mole
        * (atmospheric_pressure / standard_pressure)
        * (celsius_to_kelvin / temperature_kelvin)
    )


def calculate_specific_heat_air(
    temperature: NDArray[np.float64],
    molar_heat_capacity_air: float,
    specific_heat_equ_factors: list[float],
) -> NDArray[np.float64]:
    """Calculate temperature-dependent specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: Air temperature, [C]
        molar_heat_capacity_air: Molar heat capacity of air, [J mol-1 C-1]
        specific_heat_equ_factors: Factors in calculation of molar specific heat of air

    Returns:
        specific heat of air at constant pressure, [J mol-1 K-1]
    """
    return (
        specific_heat_equ_factors[0] * temperature**2
        + specific_heat_equ_factors[1] * temperature
        + molar_heat_capacity_air
    )


def calculate_zero_plane_displacement(
    canopy_height: NDArray[np.float64],
    plant_area_index: NDArray[np.float64],
    zero_plane_scaling_parameter: float,
) -> NDArray[np.float64]:
    """Calculate zero plane displacement height, [m].

    The zero plane displacement height is a concept used in micrometeorology to describe
    the flow of air near the ground or over surfaces like a forest canopy or crops. It
    represents the height above the actual ground where the wind speed is theoretically
    reduced to zero due to the obstruction caused by the roughness elements (like trees
    or buildings). Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        plant_area_index: Total plant area index, [m m-1]
        zero_plane_scaling_parameter: Control parameter for scaling d/h, dimensionless
            :cite:p:`raupach_simplified_1994`

    Returns:
        Zero plane displacement height, [m]
    """

    # Select grid cells where vegetation is present
    displacement = np.where(plant_area_index > 0, plant_area_index, np.nan)

    # Calculate zero displacement height
    scale_displacement = np.sqrt(zero_plane_scaling_parameter * displacement)
    zero_plane_displacement = (
        (1 - (1 - np.exp(-scale_displacement)) / scale_displacement) * canopy_height,
    )

    # No displacement in absence of vegetation
    return np.nan_to_num(zero_plane_displacement, nan=0.0).squeeze()


def calculate_roughness_length_momentum(
    canopy_height: NDArray[np.float64],
    plant_area_index: NDArray[np.float64],
    zero_plane_displacement: NDArray[np.float64],
    diabatic_correction_heat: NDArray[np.float64],
    substrate_surface_drag_coefficient: float,
    drag_coefficient: float,
    min_roughness_length: float,
    von_karman_constant: float,
) -> NDArray[np.float64]:
    """Calculate roughness length governing momentum transfer, [m].

    Roughness length is defined as the height at which the mean velocity is zero due to
    substrate roughness. Real surfaces such as the ground or vegetation are not smooth
    and often have varying degrees of roughness. Roughness length accounts for that
    effect. Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        plant_area_index: Total plant area index, [m m-1]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        diabatic_correction_heat: Diabatic correction factor for heat
        substrate_surface_drag_coefficient: Substrate-surface drag coefficient,
            dimensionless
        drag_coefficient: drag coefficient
        min_roughness_length: Minimum roughness length, [m]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        Momentum roughness length, [m]
    """

    # Calculate ratio of wind velocity to friction velocity
    ratio_wind_to_friction_velocity = np.sqrt(
        substrate_surface_drag_coefficient + (drag_coefficient * plant_area_index) / 2
    )

    # calculate initial roughness length
    initial_roughness_length = (
        (canopy_height - zero_plane_displacement)
        * np.exp(-von_karman_constant / ratio_wind_to_friction_velocity)
        * np.exp(diabatic_correction_heat)
    )

    # If roughness smaller than the substrate surface drag coefficient, set to value to
    # the substrate surface drag coefficient
    roughness_length = np.where(
        initial_roughness_length < substrate_surface_drag_coefficient,
        substrate_surface_drag_coefficient,
        initial_roughness_length,
    )
    # If roughness length in nan, zero or below sero, set to minimum value
    roughness_length = np.nan_to_num(roughness_length, nan=min_roughness_length)
    return np.where(roughness_length <= 0, min_roughness_length, roughness_length)


def calculate_monin_obukov_length(
    air_temperature: NDArray[np.float64],
    friction_velocity: NDArray[np.float64],
    sensible_heat_flux: NDArray[np.float64],
    zero_degree: float,
    specific_heat_air: float,
    density_air: float,
    von_karman_constant: float,
    gravity: float,
) -> NDArray[np.float64]:
    r"""Calculate Monin-Obukov length.

    The Monin-Obukhov length (L) is given by:

    :math:`L = -(\rho \dot cp \dot ustar**3 \dot T_{air})/(k \dot g \dot H)`

    Foken, T, 2008: Micrometeorology. Springer, Berlin, Germany.
    Note that L gets very small for very low ustar values with implications
    for subsequent functions using L as input. It is recommended to filter
    data and exclude low ustar values (ustar < ~0.2) beforehand.

    Args:
        air_temperature: Air temperature, {c}
        friction_velocity: Friction velocity, [m s-1]
        sensible_heat_flux: Sensible heat flux, [W m-2]
        zero_degree: Celsius to Kelvin conversion
        specific_heat_air: Specific heat of air, [J K-1 kg-1]
        density_air: Sensity of air, [kg m-3]
        von_karman_constant: Von karman constant, []
        gravity: Gravitational acceleration, [m s-2]

    Returns:
        Monin-Obukov length, [m]
    """
    if np.any(sensible_heat_flux == 0):
        to_raise = ValueError("The sensible heat flux must not be zero!")
        LOGGER.error(to_raise)
        raise to_raise

    temperature_kelvin = air_temperature + zero_degree
    return -(
        density_air * specific_heat_air * friction_velocity**3 * temperature_kelvin
    ) / (von_karman_constant * gravity * sensible_heat_flux)


def calculate_stability_parameter(
    reference_height: float,
    zero_plance_displacement: NDArray[np.float64],
    monin_obukov_length: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate stability parameter zeta.

    Zeta is a parameter in Monin-Obukov Theory that characterizes stratification in
    the lower atmosphere:

    zeta = (reference_height - zero_plance_displacenemt)/ monin-obukov_length

    Args:
        reference_height: Reference height, [m]
        zero_plance_displacement: Zero plance displacement height, [m]
        monin_obukov_length: Monin-Obukov length, [m]

    Returns:
        stability parameter zeta
    """
    return (reference_height - zero_plance_displacement) / monin_obukov_length


def calculate_diabatic_correction_factors(
    stability_parameter: NDArray[np.float64],
    stability_formulation: str,
) -> dict[str, NDArray[np.float64]]:
    r"""Integrated Stability Correction Functions for Heat and Momentum.

    Dimensionless stability functions needed to correct deviations from the exponential
    wind profile under non-neutral conditions. The functions give the integrated form of
    the universal functions. They depend on the value of the stability parameter
    :math:`\zeta`.
    The integration of the universal functions is:

    :math:`psi = -x * \zeta`

    for stable atmospheric conditions (:math:`\zeta >= 0`), and

    :math:`\psi = 2 * log( (1 + y) / 2)`

    for unstable atmospheric conditions (:math:`\zeta < 0`).

    The different formulations differ in their value of x and y.
    Dyer, A.J., 1974: A review of flux-profile relationships.
    Boundary-Layer Meteorology 7, 363-372.

    Dyer, A. J., Hicks, B.B., 1970: Flux-Gradient relationships in the
    constant flux layer. Quart. J. R. Meteorol. Soc. 96, 715-721.

    Businger, J.A., Wyngaard, J. C., Izumi, I., Bradley, E. F., 1971:
    Flux-Profile relationships in the atmospheric surface layer.
    J. Atmospheric Sci. 28, 181-189.

    Paulson, C.A., 1970: The mathematical representation of wind speed
    and temperature profiles in the unstable atmospheric surface layer.
    Journal of Applied Meteorology 9, 857-861.

    Foken, T, 2008: Micrometeorology. Springer, Berlin, Germany.

    Args:
        stability_parameter: Stability parameter zeta (-)
        stability_formulation: Formulation for the stability function.
        Either \code{"Dyer_1970"} or \code{"Businger_1971"}

    Returns:
        psi_h, the value of the stability function for heat and water vapor (-), and
        psi_m, the value of the stability function for momentum (-)
    """

    # Choose formulation
    if stability_formulation == "Businger_1971":
        x_h, x_m = -7.8, -6
        y_h = 0.95 * np.sqrt(1 - 11.6 * stability_parameter)
        y_m = np.power(1 - 19.3 * stability_parameter, 0.25)

    elif stability_formulation == "Dyer_1970":
        x_h, x_m = -5, -5
        y_h = np.sqrt(1 - 16 * stability_parameter)
        y_m = np.power(1 - 16 * stability_parameter, 0.25)

    else:
        raise ValueError(f"Unknown formulation: {stability_formulation}")

    psi_h = np.where(
        stability_parameter >= 0, x_h * stability_parameter, 2 * np.log((1 + y_h) / 2)
    )
    psi_m = np.where(
        stability_parameter >= 0,
        x_m * stability_parameter,
        (
            2 * np.log((1 + y_m) / 2)
            + np.log((1 + y_m**2) / 2)
            - 2 * np.arctan(y_m)
            + np.pi / 2
        ),
    )

    return {"psi_h": psi_h, "psi_m": psi_m}


def calculate_diabatic_influence_heat(
    stability_parameter: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate the diabatic influencing factor for heat.

    Args:
        stability_parameter: Stability parameter zeta

    Returns:
        Diabatic influencing factor for heat (phih)
    """
    # Initialize `phih` with zeros
    phih = np.zeros_like(stability_parameter)

    # Apply the calculation where stability_parameter < 0
    phim = np.where(
        stability_parameter < 0,
        1 / np.power((1.0 - 16.0 * stability_parameter), 0.25),
        1,  # Default value for non-negative stability_parameter to avoid indexing issue
    )
    phih_non_negative = 1 + (6.0 * stability_parameter) / (1.0 + stability_parameter)
    phih = np.where(stability_parameter < 0, np.power(phim, 2.0), phih_non_negative)

    # Clip the values of `phih` to be between 0.5 and 1.5
    return np.clip(phih, 0.5, 1.5)


def calculate_free_convection(
    leaf_dimension: float,
    sensible_heat_flux: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate free convection, gha.

    Args:
        leaf_dimension: Leaf dimension (characteristic length), [m]
        sensible_heat_flux: Sensible heat flux, [W m-2]

    Returns:
        free convection coefficient gha
    """
    d = 0.71 * leaf_dimension
    dt = 0.7045388 * np.power((d * np.power(sensible_heat_flux, 4)), 0.2)
    gha = 0.0375 * np.power(dt / d, 0.25)

    # Ensure gha is not less than 0.1
    return np.maximum(gha, 0.1)


def calculate_molar_conductance_above_canopy(
    friction_velocity: NDArray[np.float64],
    zero_plane_displacement: NDArray[np.float64],
    roughness_length_momentum: NDArray[np.float64],
    reference_height: float,
    molar_density_air: NDArray[np.float64],
    diabatic_correction_heat: NDArray[np.float64],
    minimum_conductance: float,
    von_karmans_constant: float,
) -> NDArray[np.float64]:
    r"""Calculate molar conductance above canopy, gt.

    Heat conductance, :math:`g_{t}` between any two heights :math:`z_{1}` and
    :math:`z_{0}` above-canopy is given by

    .. math::
        g_{t} = \frac {0.4 \hat{\rho} u^{*}}{ln(\frac{z_{1} - d}{z_{0} - d}) + \Psi_{H}}

    where :math:`\hat{\rho}` is the molar density or air, :math:`u^{*}` is the friction
    velocity, :math:`d` is the zero displacement height, and :math:`\Psi_{H}` is the
    diabatic correction factor for heat.

    Args:
        friction_velocity: Friction velocity[m s-1]
        zero_plane_displacement: Zero-plane displacement height, [m]
        roughness_length_momentum: Roughness length momenturm, [m]
        reference_height: Reference height, [m]
        molar_density_air: Molar density of air
        diabatic_correction_heat: Stability correction factor for heat, []
        minimum_conductance: Minimum conductance, [m s-1]
        von_karmans_constant: Von Karman constant, unitless

    Returns:
        molar conductance above canopy, [m s-1]
    """
    # Heat exchange surface height
    z0 = 0.2 * roughness_length_momentum + zero_plane_displacement
    ln = np.log(
        (reference_height - zero_plane_displacement) / (z0 - zero_plane_displacement)
    )
    molar_conductance = (
        von_karmans_constant * molar_density_air * friction_velocity
    ) / (ln + diabatic_correction_heat)

    # Ensure conductance is not less than minimum_conductance
    return np.maximum(molar_conductance, minimum_conductance)


def calculate_stomatal_conductance(
    shortwave_radiation: NDArray[np.float64],
    maximum_stomatal_conductance: float,
    half_saturation_stomatal_conductance: float,
) -> NDArray[np.float64]:
    """Calculate the stomatal conductance.

    Args:
        shortwave_radiation: Shortwave radiation absorbed by the leaves, [W m-2]
        maximum_stomatal_conductance: Maximum stomatal conductance, [mol m-2 s-1]
        half_saturation_stomatal_conductance: Half-saturation point for stomatal
            conductance, [W m-2]

    Returns:
        Stomatal conductance (gs), [mol m-2 s-1]
    """
    rpar = shortwave_radiation * 4.6  # Photosynthetically active radiation (PAR)
    return (maximum_stomatal_conductance * rpar) / (
        rpar + half_saturation_stomatal_conductance
    )


def calculate_dewpoint_temperature(
    air_temperature: NDArray[np.float64],
    effective_vapour_pressure_air: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate the dewpoint temperature.

    Args:
        air_temperature: Air temperature, [C]
        effective_vapour_pressure_air: Actual vapor pressure, [kPa]

    Returns:
        Dewpoint temperature, [C]
    """

    e0_positive = 611.2 / 1000  # e0 in kPa
    latent_heat_vapourisation = (2.501 * 10**6) - (2340 * air_temperature)
    dewpoint_temperature_positive = 1 / 273.15 - (
        461.5 / latent_heat_vapourisation
    ) * np.log(effective_vapour_pressure_air / e0_positive)

    e0_negative = 610.78 / 1000
    latent_heat_sublimation = 2.834 * 10**6
    dewpoint_temperature_negative = 1 / 273.16 - (
        461.5 / latent_heat_sublimation
    ) * np.log(effective_vapour_pressure_air / e0_negative)

    return np.where(
        air_temperature >= 0,
        1 / dewpoint_temperature_positive - 273.15,
        1 / dewpoint_temperature_negative - 273.15,
    )


def calculate_saturation_vapour_pressure(
    temperature: NDArray[np.float64],
    saturation_vapour_pressure_factors: list[float],
) -> NDArray[np.float64]:
    r"""Calculate saturation vapour pressure, kPa.

    Saturation vapour pressure :math:`e_{s} (T)` is here calculated as

    :math:`e_{s}(T) = 0.61078 exp(\frac{7.5 T}{T + 237.3})`

    where :math:`T` is temperature in degree C. (from abiotic simple model)

    Args:
        temperature: Air temperature, [C]
        saturation_vapour_pressure_factors: Factors in saturation vapour pressure
            calculation

    Returns:
        saturation vapour pressure, [kPa]
    """
    factor1, factor2, factor3 = saturation_vapour_pressure_factors
    return factor1 * np.exp((factor2 * temperature) / (temperature + factor3))


def calculate_latent_heat_vapourisation(
    temperature: NDArray[np.float64],
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factors: list[float],
) -> NDArray[np.float64]:
    """Calculate latent heat of vapourisation.

    Implementation after Eq. 8, :cite:t:`henderson-sellers_new_1984`.

    Args:
        temperature: Air temperature, [C]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        latent_heat_vap_equ_factors: Factors in calculation of latent heat of
            vapourisation

    Returns:
        latent heat of vapourisation, [kJ kg-1]
    """
    temperature_kelvin = temperature + celsius_to_kelvin
    return (
        latent_heat_vap_equ_factors[0]
        * (temperature_kelvin / (temperature_kelvin - latent_heat_vap_equ_factors[1]))
        ** 2
    ) / 1000.0


def calculate_surface_temperature(
    absorbed_shortwave_radiation: NDArray[np.float64],
    heat_conductivity: NDArray[np.float64],
    vapour_conductivity: NDArray[np.float64],
    surface_temperature: NDArray[np.float64],
    temperature_average_air_surface: NDArray[np.float64],
    atmospheric_pressure: NDArray[np.float64],
    effective_vapour_pressure_air: NDArray[np.float64],
    surface_emissivity: float,
    ground_heat_flux: NDArray[np.float64],
    relative_humidity: NDArray[np.float64],
    stefan_boltzmann_constant: float,
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factors: list[float],
    molar_heat_capacity_air: float,
    specific_heat_equ_factors: list[float],
    saturation_vapour_pressure_factors: list[float],
) -> float:
    """Calculate surface temperature with Penman-Montheith equation.

    Args:
        absorbed_shortwave_radiation: Absorbed shortwave radiation, [W m-2]
        heat_conductivity: Heat conductivity of surface
        vapour_conductivity: Vapour conductivity of surface
        surface_temperature: Surface temperature, [C]
        temperature_average_air_surface: Average between air temperature and surface
            temperature, [C]  # tair+tleaf/2
        atmospheric_pressure: Atmospheric pressure, [kPa]
        effective_vapour_pressure_air: Effective vapour pressure of air
        surface_emissivity: Surface emissivity
        ground_heat_flux: Ground heat flux, [W m-2]
        relative_humidity: Relative humidity
        stefan_boltzmann_constant: Stefan Boltzmann constant
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        latent_heat_vap_equ_factors: Factors in calculation of latent heat of
            vapourisation
        molar_heat_capacity_air: Molar heat capacity of air, [J mol-1 K-1]
        specific_heat_equ_factors: Factors in calculation of molar specific heat of air
        saturation_vapour_pressure_factors: factors in calculation of saturation vapour
            pressure

    Returns:
        surface temperature, [C]
    """

    emitted_radiation = (
        surface_emissivity
        * stefan_boltzmann_constant
        * (surface_temperature + celsius_to_kelvin) ** 4
    )
    latent_heat_vapourization = calculate_latent_heat_vapourisation(
        temperature=temperature_average_air_surface,
        celsius_to_kelvin=celsius_to_kelvin,
        latent_heat_vap_equ_factors=latent_heat_vap_equ_factors,
    )

    specific_heat_air = calculate_specific_heat_air(
        temperature=temperature_average_air_surface,
        molar_heat_capacity_air=molar_heat_capacity_air,
        specific_heat_equ_factors=specific_heat_equ_factors,
    )
    saturation_vapour_pressure = calculate_saturation_vapour_pressure(
        temperature=surface_temperature,
        saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
    )
    vapour_pressure_deficit = saturation_vapour_pressure - effective_vapour_pressure_air
    radiative_transfer = (
        4
        * surface_emissivity
        * stefan_boltzmann_constant
        * (temperature_average_air_surface + celsius_to_kelvin) ** 3
    ) / specific_heat_air

    saturation_vapour_pressure_plus = calculate_saturation_vapour_pressure(
        temperature_average_air_surface + 0.5,
        saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
    )
    saturation_vapour_pressure_minus = calculate_saturation_vapour_pressure(
        temperature=temperature_average_air_surface - 0.5,
        saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
    )
    slope_saturation_vapour_pressure_curve = (
        saturation_vapour_pressure_plus - saturation_vapour_pressure_minus
    )
    new_surface_temperature = surface_temperature + (
        (
            absorbed_shortwave_radiation
            - emitted_radiation
            - latent_heat_vapourization
            * (vapour_conductivity / atmospheric_pressure)
            * vapour_pressure_deficit
            * relative_humidity
            - ground_heat_flux
        )
        / (
            specific_heat_air * (heat_conductivity + radiative_transfer)
            + latent_heat_vapourization
            * (vapour_conductivity / atmospheric_pressure)
            * slope_saturation_vapour_pressure_curve
            * relative_humidity
        )
    )
    return new_surface_temperature


def hour_to_day(
    hourly_data: list[NDArray[np.float64]], output_statistic: str
) -> NDArray[np.float64]:
    """Compute daily statistics from hourly input data.

    Args:
        hourly_data: Hourly input data
        output_statistic: Output statistic, select "mean", "min", "max", pr "sum

    Returns:
        Daily output statistics
    """

    num_days = len(hourly_data) // 24
    daily = np.zeros_like(hourly_data)

    for i in range(num_days):
        # Extract the 24-hour block for the current day
        day_data = hourly_data[i * 24 : (i + 1) * 24]

        if output_statistic == "max":
            daily_stat = np.max(day_data)
        elif output_statistic == "min":
            daily_stat = np.min(day_data)
        elif output_statistic == "mean":
            daily_stat = np.mean(day_data)
        elif output_statistic == "sum":
            daily_stat = np.sum(day_data)
        else:
            raise ValueError(
                "Invalid statistic. Please use 'max', 'min', 'mean', or 'sum."
            )

        # Replicate the daily statistic for each hour of the day
        daily[i * 24 : (i + 1) * 24] = daily_stat

    return daily


def hour_to_day_no_replication(
    hourly_data: list[NDArray[np.float64]],
    output_statistic: str,
) -> NDArray[np.float64]:
    """Compute daily statistics from hourly input data without replicating 24 times.

    Args:
        hourly_data: Hourly input data
        output_statistic: Output statistic, select "mean", "min", "max", or "sum"

    Returns:
        List of daily output statistics
    """
    num_days = len(hourly_data) // 24
    if len(hourly_data) % 24 != 0:
        raise ValueError("Hourly data length must be a multiple of 24")

    daily = np.zeros(num_days)

    for i in range(num_days):
        day_data = hourly_data[i * 24 : (i + 1) * 24]

        if output_statistic == "max":
            daily_stat = np.max(day_data)
        elif output_statistic == "min":
            daily_stat = np.min(day_data)
        elif output_statistic == "mean":
            daily_stat = np.mean(day_data)
        elif output_statistic == "sum":
            daily_stat = np.sum(day_data)
        else:
            raise ValueError(
                "Invalid statistic. Please use 'max', 'min', 'mean', or 'sum'."
            )

        daily[i] = daily_stat

    return daily


def calculate_moving_average(
    values: list[NDArray[np.float64]],
    window_size: int,
) -> NDArray[np.float64]:
    """Compute the moving average of a list of values.

    Args:
        values: List of values
        window_size: Number of elements to include in the moving average

    Returns:
        moving average values
    """

    number_of_values = len(values)
    if window_size > number_of_values:
        raise ValueError("Window size is larger than length of data set.")

    output = np.zeros(number_of_values)

    for i in range(number_of_values):
        # Calculate the sum over the window with circular wrapping
        sum_window = np.sum(
            [
                values[(i - j + number_of_values) % number_of_values]
                for j in range(window_size)
            ]
        )
        output[i] = sum_window / window_size

    return output


def calculate_yearly_moving_average(
    hourly_values: list[NDArray[np.float64]],
    window_size: int,
) -> NDArray[np.float64]:
    """Calculate the yearly moving average from hourly input data.

    Args:
        hourly_values: List of hourly values
        window_size: Number of elements to include in the moving average

    Returns:
        List of yearly moving average values, replicated for each hour of the day.
    """
    # Calculate daily mean
    num_days = len(hourly_values) // 24
    daily_means = np.zeros(num_days)

    daily_means = np.array(
        [np.mean(hourly_values[i * 24 : (i + 1) * 24]) for i in range(num_days)]
    )

    # Calculate moving average
    moving_average_values = calculate_moving_average(
        values=daily_means, window_size=window_size
    )

    # Replicate moving average values for each hour of the day
    yearly_moving_average = []
    for daily_mean in moving_average_values:
        yearly_moving_average.extend([daily_mean] * 24)

    return yearly_moving_average


def calculate_ground_heat_flux(
    soil_surface_temperature: list[NDArray[np.float64]],
    soil_moisture: list[NDArray[np.float64]],
    bulk_density_soil: float,
    volumetric_mineral_content: float,
    volumetric_quartz_content: float,
    mass_fraction_clay: float,
    window_size_yearly: int,
    calculate_yearly_flux: bool = True,
) -> dict[str, list[float]]:
    """Calculate the ground heat flux, [W m-2].

    Args:
        soil_surface_temperature: List of soil surface temperatures, [C]
        soil_moisture: List of soil moisture values
        bulk_density_soil: Bulk density of soil
        volumetric_mineral_content: Volumetric minearal content of soil
        volumetric_quartz_content: Volumetric quarz content of soil
        mass_fraction_clay: Mass fraction of clay
        calculate_yearly_flux: Flag to determine if yearly ground flux should be
            calculated.
        window_size_yearly: Size of moving average window for annual averaging

    Returns:
        Dictionary containing ground heat flux, min/man ground heat flux
    """

    # Prepare output lists
    ground_heat_flux_out = []
    min_ground_heat_flux_out = []
    max_ground_heat_flux_out = []

    # Precompute time invariant variables for thermal conductivity calculation
    frs = volumetric_mineral_content + volumetric_quartz_content
    c1 = (
        0.57 + 1.73 * volumetric_quartz_content + 0.93 * volumetric_mineral_content
    ) / (
        1 - 0.74 * volumetric_quartz_content - 0.49 * volumetric_mineral_content
    ) - 2.8 * frs * (1 - frs)
    c3 = 1 + 2.6 * np.power(mass_fraction_clay, -0.5)
    c4 = 0.03 + 0.7 * frs**2
    mu1 = 2400 * bulk_density_soil / 2.64
    mu2 = 1.06 * bulk_density_soil

    for temperature, moisture in zip(soil_surface_temperature, soil_moisture):
        # Calculate daily mean soil surface temperature
        daily_mean_soil_surface_temperature = hour_to_day(
            hourly_data=temperature, output_statistic="mean"
        )

        # Vectorize the number of hours
        num_hours = len(temperature)

        # Prepare arrays
        moisture_array = np.array(moisture)
        temperature_array = np.array(temperature)

        specific_heat_soil = mu1 + 4180 * moisture_array
        volumetric_density_soil = (
            bulk_density_soil * (1 - moisture_array) + moisture_array
        ) * 1000
        c2 = mu2 * moisture_array

        # Calculate thermal conductivity
        thermal_conductivity = (
            c1 + c2 * moisture_array - (c1 - c4) * np.exp(-((c3 * moisture_array) ** 4))
        )

        # Avoid division by zero when calculating thermal diffusivity
        thermal_diffusivity = np.where(
            specific_heat_soil * volumetric_density_soil != 0,
            thermal_conductivity / (specific_heat_soil * volumetric_density_soil),
            0.001,
        )

        daily_angular_frequency = (2 * np.pi) / (24 * 3600)
        diurnal_damping_depth = np.sqrt(
            2 * thermal_diffusivity / daily_angular_frequency
        )
        soil_diffusivity = (
            np.sqrt(2) * (thermal_conductivity / diurnal_damping_depth) * 0.5
        )

        # Calculate temperature fluctuations
        daily_surface_temperature_fluctuations = (
            temperature_array - daily_mean_soil_surface_temperature
        )

        # Calculate moving averages
        daily_soil_diffusivity = calculate_moving_average(soil_diffusivity, 6)
        ground_heat_flux_avg = calculate_moving_average(
            daily_surface_temperature_fluctuations, 6
        )
        ground_heat_flux = (
            np.array(ground_heat_flux_avg) * np.array(daily_soil_diffusivity) * 1.1171
        )

        # Calculate min/max ground heat flux
        min_ground_heat_flux = hour_to_day(ground_heat_flux, output_statistic="min")
        max_ground_heat_flux = hour_to_day(ground_heat_flux, output_statistic="max")

        # Apply min/max constraints
        ground_heat_flux = np.clip(
            ground_heat_flux, min_ground_heat_flux, max_ground_heat_flux
        )

        if calculate_yearly_flux:
            # Calculate yearly moving averages
            thermal_conductivity_yearly_moving_average = (
                calculate_yearly_moving_average(
                    thermal_conductivity, window_size=window_size_yearly
                )
            )
            thermal_diffusivity_moving_average = calculate_yearly_moving_average(
                thermal_diffusivity, window_size=window_size_yearly
            )

            yearly_angular_frequency = (2 * np.pi) / (num_hours * 3600)
            yearly_soil_diffusivity = np.where(
                thermal_diffusivity_moving_average != 0,
                np.sqrt(2)
                * np.array(thermal_conductivity_yearly_moving_average)
                / np.sqrt(
                    2
                    * np.array(thermal_diffusivity_moving_average)
                    / yearly_angular_frequency
                ),
                0.001,
            )

            yearly_mean_soil_surface_temperature = np.mean(
                daily_mean_soil_surface_temperature
            )
            yearly_surface_temperature_fluctuations = (
                daily_mean_soil_surface_temperature
                - yearly_mean_soil_surface_temperature
            )
            moving_average_yearly_surface_temperature_fluctuations = (
                calculate_yearly_moving_average(
                    yearly_surface_temperature_fluctuations,
                    window_size=window_size_yearly,
                )
            )
            ground_heat_flux += (
                moving_average_yearly_surface_temperature_fluctuations
                * yearly_soil_diffusivity
                * 1.1171
            )

        # Store results
        ground_heat_flux_out.append(ground_heat_flux)
        min_ground_heat_flux_out.append(min_ground_heat_flux)
        max_ground_heat_flux_out.append(max_ground_heat_flux)

    return {
        "ground_heat_flux": ground_heat_flux_out,
        "min_ground_heat_flux": min_ground_heat_flux_out,
        "max_ground_heat_flux": max_ground_heat_flux_out,
    }


#  UP TO HERE, ALL SHOULD WORK. CHECK TOP TO BOTTOM ASSUMPTIONS
# # Big leaf model
# def big_leaf_model(
#     timestep: dict[str, int],
#     climate_data: dict[str, NDArray[np.float64]],
#     vegetation_parameters: list[float],
#     ground_parameters: list[float],
#     soil_moisture: list[float],
#     latitude: float,
#     longitude: float,
#     max_surface_air_temperature_difference: float,
#     reference_height: float,
#     max_iterations: int,
#     bwgt: float,
#     tolerance: float,
#     # gmn: float, unused
#     calculate_yearly_flux: bool,
#     core_constants: CoreConsts,
#     abiotic_constants: AbioticConsts,
#     abiotic_simple_constants: AbioticSimpleConsts,
# ) -> dict[str, NDArray[np.float64]]:
#     """Run Big leaf model for one time step.

#     TODO check how the iterations work re convergence and over a whole month
#     TODO find out wat bwgt is
#     TODO set typing to work with numpy arrays
#     TODO check that functions run ok with numpy arrays, atm some of if's will break
#     TODO add tests
#     TODO to numpy
#     TODO check order (top to bottom)

#     Args:
#         timestep: Date and time
#         climate_data: Input climate data
#         vegetation_parameters: Vegetation parameters
#         ground_parameters: Ground parameters
#         soil_moisture: Soil moisture
#         latitude: Latitude in degrees
#         longitude: Longitude in degrees
#         max_surface_air_temperature_difference: Maximum amount (degrees C) by whichthe
#             vegetation heat exchange surface of the canopy can exceed air temperature
#         reference_height: Reference height, [m]
#         max_iterations: Maximum number of iterations over which to run the model to
#             ensure convergence
#         bwgt: ??=0.5,
#         tolerance: Tolerance for convergence
#         calculate_yearly_flux: Flag to determine if yearly ground flux should be
#             calculated.
#         core_constants: Set of constants shared across all models
#         abiotic_constants: Set of constants for abiotic model
#         abiotic_simple_constants: Set of constants for abiotic simple model

#     Returns:
#         dictionary with results from energy balance
#     """

#     # Unpack timestep DataFrame
#     year = np.array(timestep["year"])
#     month = np.array(timestep["month"])
#     day = np.array(timestep["day"])
#     local_time = np.array(timestep["hour"])

#     # Unpack climate_data DataFrame
#     air_temperature = np.array(climate_data["temp"])
#     relative_humidity = np.array(climate_data["relhum"])
#     atmospheric_pressure = np.array(climate_data["pres"])
#     shortwave_radiation_down = np.array(climate_data["swdown"])
#     diffuse_radiation_down = np.array(climate_data["difrad"])
#     longwave_radiation_down = np.array(climate_data["lwdown"])
#     wind_speed = np.array(climate_data["windspeed"])
#     # wind_direction = np.array(climate_data["winddir"])
#     # precipitation = np.array(climate_data["precip"])

#     # Unpack vegetation_parameters
#     (
#         canopy_height,
#         plant_area_index,
#         leaf_inclination_angle_coefficient,
#         leaf_orientation_coefficient,
#         clumping_factor,
#         leaf_reluctance_shortwave,
#         leaf_transmittance_shortwave,
#         leaf_dimension,
#         leaf_emissivity,
#         maximum_stomatal_conductance,
#         half_saturation_stomatal_conductance,
#     ) = vegetation_parameters

#     # Unpack ground_parameters
#     (
#         ground_reflectance,
#         slope,
#         aspect,
#         ground_emissivity,
#         bulk_density,
#         volumetric_mineral_content,
#         volumetric_quartz_content,
#         mass_fraction_clay,
#         soil_moisture_residual,
#         soil_moisture_capacity,
#     ) = ground_parameters

#     # Calculate absorbed shortwave radiation
#     absorbed_shortwave_radiation = calculate_absorbed_shortwave_radiation(
#         plant_area_index=plant_area_index,
#         leaf_orientation_coefficient=leaf_orientation_coefficient,
#         leaf_reluctance_shortwave=leaf_reluctance_shortwave,
#         leaf_transmittance_shortwave=leaf_transmittance_shortwave,
#         clumping_factor=clumping_factor,
#         ground_reflectance=ground_reflectance,
#         slope=slope,
#         aspect=aspect,
#         latitude=latitude,
#         longitude=longitude,
#         year=year,
#         month=month,
#         day=day,
#         local_time=local_time,
#         shortwave_radiation=shortwave_radiation_down,
#         diffuse_radiation=diffuse_radiation_down,
#         leaf_inclination_angle_coefficient=leaf_inclination_angle_coefficient,
#     )

#     # Calculate time-invariant variables
#     adjusted_plant_area_index = plant_area_index / (1 - clumping_factor)

#     radiation_transmission_coefficient = (1 - clumping_factor**2) * np.exp(
#         -adjusted_plant_area_index
#     ) + clumping_factor**2
#     zero_plane_displacement = calculate_zero_plane_displacement(
#         canopy_height=canopy_height,
#         plant_area_index=plant_area_index,
#         zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
#     )
#  # Used to avoid (h-d)/zm being less than one, meaning log((h-d)/zm) becomes negative
#     drag_limit = core_constants.von_karmans_constant / np.sqrt(
#         abiotic_constants.substrate_surface_drag_coefficient
#         + (abiotic_constants.drag_coefficient * plant_area_index) / 2
#     )

#     # Initialize variables
#     ground_temperature = np.copy(air_temperature)
#     canopy_temperature = np.copy(air_temperature)
#     temperature_average_air_canopy = np.copy(air_temperature)
#     temperature_average_air_ground = np.copy(air_temperature)
#     psim = np.zeros(len(shortwave_radiation_down))
#     psih = np.zeros(len(shortwave_radiation_down))
#     phih = np.zeros(len(shortwave_radiation_down))
#     monin_obukov_length = np.zeros(len(shortwave_radiation_down))
#     ground_heat_flux = np.zeros(len(shortwave_radiation_down))
#     # min_ground_heat_flux = np.full(len(shortwave_radiation_down), -999.0)
#     # max_ground_heat_flux = np.full(len(shortwave_radiation_down), 999.0)
#     friction_velocity = np.full(len(shortwave_radiation_down), 999.0)
#     ground_shortwave_absorption = np.full(len(shortwave_radiation_down), 999.0)

#     # New variables
#     sensible_heat_flux = (
#         0.5 * shortwave_radiation_down
#         - leaf_emissivity
#         * core_constants.stefan_boltzmann_constant
#         * (air_temperature + core_constants.zero_Celsius) ** 4
#     )
#     tstf = tolerance * 2
#     iteration = 0
#     tst = 0

#     while tstf > tolerance:
#         tst = 0
#         for i, _ in enumerate(shortwave_radiation_down):
#             # Calculate longwave radiation
#             # Longwave emission from canopy
#             canopy_longwave_emission = (
#                 leaf_emissivity
#                 * core_constants.stefan_boltzmann_constant
#                 * (canopy_temperature[i] + core_constants.zero_Celsius) ** 4
#             )
#             # longwave radiation from the sky
#             longwave_downward_radiation_sky = (
#                 leaf_emissivity * longwave_radiation_down[i]
#             )
#             # longwave radiation from ground
#             ground_longwave_radiation = ground_emissivity * (
#                 radiation_transmission_coefficient * longwave_downward_radiation_sky
#                 + (1 - radiation_transmission_coefficient) * canopy_longwave_emission
#             )

#             # Calculate absorbed radiation
#             ground_shortwave_absorption[i] = (
#                 absorbed_shortwave_radiation["ground"][i] + ground_longwave_radiation
#             )
#             canopy_shortwave_absorption = (
#                 absorbed_shortwave_radiation["canopy"][i]
#                 + longwave_downward_radiation_sky
#             )

#             # Calculate canopy temperature
#             roughness_length_momentum = calculate_roughness_length_momentum(
#                 canopy_height=canopy_height,
#                 plant_area_index=plant_area_index,
#                 zero_plane_displacement=zero_plane_displacement,
#                 diabatic_correction_heat=psih,
#                 substrate_surface_drag_coefficient=(
#                     abiotic_constants.substrate_surface_drag_coefficient
#                 ),
#                 drag_coefficient=abiotic_constants.drag_coefficient,
#                 min_roughness_length=abiotic_constants.min_roughness_length,
#                 von_karman_constant=core_constants.von_karmans_constant,
#             )

#             # Calculate friction velocity
#             friction_velocity[i] = (
#                 core_constants.von_karmans_constant * wind_speed[i]
#             ) / (
#                 np.log(
#                     (reference_height - zero_plane_displacement)
#                     / roughness_length_momentum
#                 )
#                 + psim[i]
#             )
#             friction_velocity[i] = np.where(
#                 friction_velocity[i] < abiotic_constants.min_friction_velocity,
#                 abiotic_constants.min_friction_velocity,
#                 friction_velocity[i],
#             )

#             # Calculate conductivities
#             free_convection = calculate_free_convection(
#                 leaf_dimension=leaf_dimension,
#                 sensible_heat_flux=abs(sensible_heat_flux[i]),
#             )

#             minimum_conductance = free_convection * 2 * plant_area_index

#             molar_density_air = calculate_molar_density_air(
#                 temperature=temperature_average_air_canopy[i],
#                 atmospheric_pressure=atmospheric_pressure[i],
#                 standard_mole=core_constants.standard_mole,
#                 standard_pressure=core_constants.standard_pressure,
#                 celsius_to_kelvin=core_constants.zero_Celsius,
#             )

#             air_heat_conductivity = calculate_molar_conductance_above_canopy(
#                 friction_velocity=friction_velocity[i],
#                 zero_plane_displacement=zero_plane_displacement,
#                 roughness_length_momentum=roughness_length_momentum,
#                 reference_height=reference_height,
#                 molar_density_air=molar_density_air,
#                 diabatic_correction_heat=psih[i],
#                 minimum_conductance=minimum_conductance,
#                 von_karmans_constant=core_constants.von_karmans_constant,
#             )

#             stomatal_conductivity = calculate_stomatal_conductance(
#                 shortwave_radiation=shortwave_radiation_down[i],
#                 maximum_stomatal_conductance=maximum_stomatal_conductance * 3,
#                 half_saturation_stomatal_conductance=(
#                     half_saturation_stomatal_conductance * 3
#                 ),
#             )

#             leaf_vapour_conductivity = 1 / (
#                 1 / air_heat_conductivity + 1 / stomatal_conductivity
#             )

#             if stomatal_conductivity == 0:
#                 leaf_vapour_conductivity = 0

#             # Calculate new canopy temperature
#             saturation_vapour_pressure = calculate_saturation_vapour_pressure(
#                 temperature=air_temperature[i],
#                 saturation_vapour_pressure_factors=(
#                     abiotic_simple_constants.saturation_vapour_pressure_factors
#                 ),
#             )
#             effective_vapour_pressure_air = (
#                 saturation_vapour_pressure * relative_humidity[i] / 100
#             )

#             canopy_temperature_new = calculate_surface_temperature(
#                 absorbed_shortwave_radiation=canopy_shortwave_absorption,
#                 heat_conductivity=air_heat_conductivity,
#                 vapour_conductivity=leaf_vapour_conductivity,
#                 surface_temperature=air_temperature[i],  # ?
#                 temperature_average_air_surface=temperature_average_air_canopy[i],
#                 atmospheric_pressure=atmospheric_pressure[i],
#                 effective_vapour_pressure_air=effective_vapour_pressure_air,
#                 surface_emissivity=leaf_emissivity,
#                 ground_heat_flux=ground_heat_flux[i],
#                 relative_humidity=relative_humidity[i],
#                 stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
#                 celsius_to_kelvin=core_constants.zero_Celsius,
#                 latent_heat_vap_equ_factors=(
#                     abiotic_constants.latent_heat_vap_equ_factors
#                 ),
#                 molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#                 specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#                 saturation_vapour_pressure_factors=(
#                     abiotic_simple_constants.saturation_vapour_pressure_factors
#                 ),
#             )

#             dewpoint_temperature = calculate_dewpoint_temperature(
#                 air_temperature=air_temperature[i],
#                 effective_vapour_pressure_air=effective_vapour_pressure_air,
#             )
#             canopy_temperature_new = np.where(
#                 canopy_temperature_new < dewpoint_temperature,
#                 dewpoint_temperature,
#                 canopy_temperature_new,
#             )

#             # Calculate ground surface temperature
#             soil_relative_humidity = (soil_moisture[i] - soil_moisture_residual) / (
#                 soil_moisture_capacity - soil_moisture_residual
#             )
#             ground_temperature_new = calculate_surface_temperature(
#                 absorbed_shortwave_radiation=ground_shortwave_absorption[i],
#                 heat_conductivity=air_heat_conductivity,  # TODO micropoint uses gHa
#                 vapour_conductivity=air_heat_conductivity,  # not sure why ??
#                 surface_temperature=temperature_average_air_ground[i],  # ?
#                 temperature_average_air_surface=temperature_average_air_canopy[i],
#                 atmospheric_pressure=atmospheric_pressure[i],
#                 effective_vapour_pressure_air=effective_vapour_pressure_air,
#                 surface_emissivity=ground_emissivity,  # ??
#                 ground_heat_flux=ground_heat_flux[i],
#                 relative_humidity=soil_relative_humidity,
#                 stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
#                 celsius_to_kelvin=core_constants.zero_Celsius,
#                 latent_heat_vap_equ_factors=(
#                     abiotic_constants.latent_heat_vap_equ_factors
#                 ),
#                 molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#                 specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#                 saturation_vapour_pressure_factors=(
#                     abiotic_simple_constants.saturation_vapour_pressure_factors
#                 ),
#             )
#             if ground_temperature_new < dewpoint_temperature:
#                 ground_temperature_new = dewpoint_temperature

#             # Cap values
#             difference_canopy_air_temperature = (
#                 canopy_temperature_new - air_temperature[i]
#             )
#             difference_ground_air_temperature = (
#                 ground_temperature_new - air_temperature[i]
#             )
#             difference_canopy_air_temperature = np.where(
#                 difference_canopy_air_temperature
#                 > max_surface_air_temperature_difference,
#                 max_surface_air_temperature_difference,
#                 difference_canopy_air_temperature,
#             )
#             difference_ground_air_temperature = np.where(
#                 difference_ground_air_temperature
#                 > max_surface_air_temperature_difference,
#                 max_surface_air_temperature_difference,
#                 difference_ground_air_temperature,
#             )
#             canopy_temperature_new = (
#                 air_temperature[i] + difference_canopy_air_temperature
#             )
#             ground_temperature_new = (
#                 air_temperature[i] + difference_ground_air_temperature
#             )

#             # Run tests for convergence
#             tst2 = abs(canopy_temperature_new - canopy_temperature[i])
#             tst3 = abs(ground_temperature_new - ground_temperature[i])
#             if tst2 > tst:
#                 tst = tst2
#             if tst3 > tst:
#                 tst = tst3

#             # Reassign canopy_temperature and ground_temperature using bwgt
#             canopy_temperature[i] = (
#                 bwgt * canopy_temperature[i] + (1 - bwgt) * canopy_temperature_new
#             )
#             ground_temperature[i] = (
#                 bwgt * ground_temperature[i] + (1 - bwgt) * ground_temperature_new
#             )

#             # Recalculate variables
#             temperature_average_air_canopy[i] = (
#                 canopy_temperature[i] + air_temperature[i]
#             ) / 2
#             temperature_average_air_ground[i] = (
#                 ground_temperature[i] + air_temperature[i]
#             ) / 2
#             temperature_average_air_canopy_kelvin = (
#                 core_constants.zero_Celsius + temperature_average_air_canopy[i]
#             )
#             molar_density_air = calculate_molar_density_air(
#                 temperature=temperature_average_air_canopy[i],
#                 atmospheric_pressure=atmospheric_pressure[i],
#                 standard_mole=core_constants.standard_mole,
#                 standard_pressure=core_constants.standard_pressure,
#                 celsius_to_kelvin=core_constants.zero_Celsius,
#             )
#             specific_heat_air = calculate_specific_heat_air(
#                 temperature=temperature_average_air_canopy[i],
#                 molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#                 specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#             )

#             # Calculate sensible heat flux
#             sensible_heat_flux[i] = bwgt * sensible_heat_flux[i] + (1 - bwgt) * (
#                 air_heat_conductivity
#                 * specific_heat_air
#                 * (canopy_temperature_new - air_temperature[i])
#             )

#             # Set limits to sensible heat flux
#             net_radiation = (
#                 canopy_shortwave_absorption
#                 - core_constants.stefan_boltzmann_constant
#                 * leaf_emissivity
#                 * (canopy_temperature[i] + 273.15) ** 4
#             )
#             if net_radiation > 0 and sensible_heat_flux[i] > net_radiation:
#                 sensible_heat_flux[i] = net_radiation

#             # Recalculate stability variables
#             monin_obukov_length[i] = calculate_monin_obukov_length(
#                 air_temperature=temperature_average_air_canopy_kelvin,
#                 friction_velocity=friction_velocity[i],
#                 sensible_heat_flux=sensible_heat_flux,
#                 zero_degree=core_constants.zero_Celsius,
#                 specific_heat_air=specific_heat_air,
#                 density_air=molar_density_air,
#                 von_karman_constant=core_constants.von_karmans_constant,
#                 gravity=core_constants.gravity,
#             )

#             stability_parameter = calculate_stability_parameter(
#                 reference_height=reference_height,
#                 zero_plance_displacement=zero_plane_displacement,
#                 monin_obukov_length=monin_obukov_length,
#             )

#             psih[i], psim[i] = calculate_diabatic_correction_factors(
#                 stability_parameter=stability_parameter,
#                 stability_formulation="Businger_1971",  # TODO
#             )

#             phih[i] = calculate_diabatic_influence_heat(
#                 stability_parameter=stability_parameter,
#             )

#             # Set limits to diabatic coefficients
#             ln1 = np.log(
#                 (reference_height - zero_plane_displacement) /
# roughness_length_momentum
#             )
#             ln2 = np.log(
#                 (reference_height - zero_plane_displacement)
#                 / (abiotic_constants.drag_coefficient * roughness_length_momentum)
#             )
#             if psim[i] < -0.9 * ln1:
#                 psim[i] = -0.9 * ln1
#             if psih[i] < -0.9 * ln2:
#                 psih[i] = -0.9 * ln2
#             if psim[i] > 0.9 * ln1:
#                 psim[i] = 0.9 * ln1
#             if psih[i] > 0.9 * ln2:
#                 psih[i] = 0.9 * ln2
#             if psih[i] > 0.9 * drag_limit:
#                 psih[i] = 0.9 * drag_limit

#         # Recalculate Ground heat flux
#         new_ground_heat_flux = calculate_ground_heat_flux(
#             soil_surface_temperature=ground_temperature[i],
#             soil_moisture=soil_moisture,
#             bulk_density_soil=bulk_density,
#             volumetric_mineral_content=volumetric_mineral_content,
#             volumetric_quartz_content=volumetric_quartz_content,
#             mass_fraction_clay=mass_fraction_clay,
#             calculate_yearly_flux=calculate_yearly_flux,
#             #  Gmax, Gmin, iter??
#         )
#         ground_heat_flux = new_ground_heat_flux["ground_heat_flux"]
#         # min_ground_heat_flux = new_ground_heat_flux["min_ground_heat_flux"]
#         # max_ground_heat_flux = new_ground_heat_flux["max_ground_heat_flux"]

#         tstf = tst
#         iteration += 1
#         if iteration >= max_iterations:
#             tstf = 0

#     # Return outputs
#     return {
#         "canopy_temperature": canopy_temperature,
#         "ground_temperature": ground_temperature,
#         "sensible_heat_flux": sensible_heat_flux,
#         "ground_heat_flux": ground_heat_flux,
#         "psih": psih,
#         "psim": psim,
#         "phih": phih,
#         "monin_obukov_length": monin_obukov_length,
#         "friction_velocity": friction_velocity,
#         "ground_shortwave_absorption": ground_shortwave_absorption,
#         "err": [tst],
#         "albedo": absorbed_shortwave_radiation["albedo"],
#     }


# def weather_height_adjustment(
#     timestep: dict[str, int],
#     climate_data: dict[str, NDArray[np.float64]],
#     canopy_height: float,
#     plant_area_index: float,
#     reference_height_in: float,
#     wind_reference_height_in: float,
#     reference_height_out: float,
#     latitude: float,
#     longitude: float,
#     core_constants: CoreConsts,
#     abiotic_constants: AbioticConsts,
#     abiotic_simple_constants: AbioticSimpleConsts,
# ) -> dict[str, NDArray[np.float64]]:
#     """Adjust height of climate input data."""

#     air_temperature = climate_data["temp"].values
#     relative_humidity = climate_data["relhum"].values
#     wind_speed = climate_data["windspeed"].values

#     vegetation_parameters = [0.12, 1, 1, 0.1, 0.4, 0.2, 0.05, 0.97, 0.33, 100.0]
#     ground_parameters = [
#         0.15,
#         0.0,
#         180.0,
#         0.97,
#         1.529643,
#         0.509,
#         0.06,
#         0.5422,
#         5.2,
#         -5.6,
#         0.419,
#         0.074,
#     ]
#     soil_moisture = np.full_like(
#         air_temperature, 0.2
#     )  # Initialize soilm with size and value 0.2

#     # Run point model
#     bigleaf = {
#         "air_temperature": np.full_like(air_temperature, 20.0)
#     }  # TODO insert function

#     # Extract things needed from list
#     psih = bigleaf["psih"]
#     bigleaf_air_temperature = bigleaf["air_temperature"]

#     # Define variables
#     adjusted_air_temperature = np.zeros_like(air_temperature)
#     adjusted_relative_humidity = np.zeros_like(air_temperature)
#     adjusted_wind_speed = np.zeros_like(air_temperature)

#     # Zero-plane displacement
#     zero_plane_displacement = calculate_zero_plane_displacement(
#         canopy_height=canopy_height,
#         plant_area_index=plant_area_index,
#         zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
#     )

#     for i, _ in enumerate(air_temperature):
#         roughness_length_momentum = calculate_roughness_length_momentum(
#             canopy_height=canopy_height,
#             plant_area_index=plant_area_index,
#             zero_plane_displacement=zero_plane_displacement,
#             diabatic_correction_heat=psih[i],
#             substrate_surface_drag_coefficient=(
#                 abiotic_constants.substrate_surface_drag_coefficient
#             ),
#             drag_coefficient=abiotic_constants.drag_coefficient,
#             min_roughness_length=abiotic_constants.min_roughness_length,
#             von_karman_constant=core_constants.von_karmans_constant,
#         )
#         adjustment_height = (
#             abiotic_constants.drag_coefficient * roughness_length_momentum
#         )
#         log_profile_reference_height = np.log(
#             (reference_height_out - zero_plane_displacement) / adjustment_height
#         ) / np.log((reference_height_in - zero_plane_displacement) /
# adjustment_height)

#         # Temperature
#         adjusted_air_temperature[i] = (
#             bigleaf_air_temperature[i] - air_temperature[i]
#         ) * (1 - log_profile_reference_height) + air_temperature[i]

#         # Humidity
#         saturation_vapour_pressure_in = calculate_saturation_vapour_pressure(
#             air_temperature[i],
#             saturation_vapour_pressure_factors=(
#                 abiotic_simple_constants.saturation_vapour_pressure_factors
#             ),
#         )
#         effective_vapour_pressure_air = (
#             saturation_vapour_pressure_in * relative_humidity[i] / 100
#         )
#         saturation_vapour_pressure_bigleaf = calculate_saturation_vapour_pressure(
#             bigleaf_air_temperature[i],
#             saturation_vapour_pressure_factors=(
#                 abiotic_simple_constants.saturation_vapour_pressure_factors
#             ),
#         )
#         saturation_vapour_pressure_adjusted = effective_vapour_pressure_air + (
#             saturation_vapour_pressure_bigleaf - effective_vapour_pressure_air
#         ) * (1 - log_profile_reference_height)
#         saturation_vapour_pressure_adjusted = calculate_saturation_vapour_pressure(
#             adjusted_air_temperature[i],
#             saturation_vapour_pressure_factors=(
#                 abiotic_simple_constants.saturation_vapour_pressure_factors
#             ),
#         )
#         adjusted_relative_humidity[i] = (
#             saturation_vapour_pressure_adjusted / saturation_vapour_pressure_bigleaf
#         ) * 100

#         # Wind speed
#         log_profile_wind_reference_height = np.log(
#          (reference_height_out - zero_plane_displacement) / roughness_length_momentum
#         ) / np.log(
#             (wind_reference_height_in - zero_plane_displacement)
#             / roughness_length_momentum
#         )
#         adjusted_wind_speed[i] = wind_speed[i] * log_profile_wind_reference_height

#     # Create a copy of climdata to avoid overwriting original input
#     climdata_copy = climate_data.copy()
#     climdata_copy["temp"] = adjusted_air_temperature
#     climdata_copy["relhum"] = adjusted_relative_humidity
#     climdata_copy["windspeed"] = adjusted_wind_speed

#     return climdata_copy


def calculate_soil_moisture(
    air_temperature: NDArray[np.float64],
    shortwave_radiation_down: NDArray[np.float64],
    longwave_radiation_down: NDArray[np.float64],
    precipitation: NDArray[np.float64],
    infiltration_rate: float,
    evaporation_rate: float,
    pwr: float,
    soil_moisture_capacity: float,
    soil_moisture_residual: float,
    saturated_hydraulic_conductivity: float,
    a: float,
) -> NDArray[np.float64]:
    """Simple soil moisture bucket model.

    Similar but simpler to our hydrology model, can be replaced, works on daily basis.
    TODO where is the initial soil moisture value?

    Args:
        air_temperature: Air temperature, [C]
        shortwave_radiation_down: Shortwave downward radiation, [W m-2]
        longwave_radiation_down: Longwave downward radiation, [W m-2]
        precipitation: Precipitation, [mm]
        infiltration_rate: Factor that affects infiltration of water in topsoil
        evaporation_rate: Factor that affects evaporation from topsoil
        pwr: Parameter in calculation of hydraulic conductivity
        soil_moisture_capacity: Soil moisture capacity, vol
        soil_moisture_residual: Soil moisture residual, vol
        saturated_hydraulic_conductivity: float,
        a: Parameter in calculation of soil moisture distribution

    Returns:
        soil moisture for two layers, vol
    """

    # Calculate net radiation
    shortwave_radiation = (1 - 0.15) * shortwave_radiation_down
    longwave_radiation_out = (
        5.67 * 10**-8 * 0.95 * np.power(air_temperature + 273.15, 4)
    )
    longwave_net_radiation = longwave_radiation_out - longwave_radiation_down
    net_radiation = np.maximum(shortwave_radiation - longwave_net_radiation, 0)

    # Convert to daily values
    daily_net_radiation = hour_to_day(net_radiation, "mean")
    daily_precipitation = hour_to_day(precipitation, "sum")

    # Run soil model
    soil_moisture = np.zeros_like(daily_precipitation)
    top_soil_layer = soil_moisture_capacity
    lowertop_soil_layer = soil_moisture_capacity
    soil_moisture[0] = soil_moisture_capacity

    for i in range(1, len(daily_precipitation)):
        average_saturation = (top_soil_layer + lowertop_soil_layer) / 2
        saturation_difference = lowertop_soil_layer - top_soil_layer
        top_soil_layer = (
            top_soil_layer
            + infiltration_rate * daily_precipitation[i]
            - evaporation_rate * daily_net_radiation[i]
        )
        hydraulic_conductivity = saturated_hydraulic_conductivity * np.power(
            average_saturation / soil_moisture_capacity, pwr
        )
        top_soil_layer = (
            top_soil_layer + a * hydraulic_conductivity * saturation_difference
        )
        lowertop_soil_layer = (
            lowertop_soil_layer
            - (a * hydraulic_conductivity * saturation_difference) / 10
        )

        # Enforce bounds
        top_soil_layer = np.clip(
            top_soil_layer, soil_moisture_residual, soil_moisture_capacity
        )
        lowertop_soil_layer = np.clip(
            lowertop_soil_layer, soil_moisture_residual, soil_moisture_capacity
        )

        soil_moisture[i] = (top_soil_layer + lowertop_soil_layer) / 2

    return soil_moisture


# THE FOLLOWING IS NOT TESTED
def calculate_shortwave_radiation_below_canopy(
    latitude: NDArray[np.float64],
    longitude: NDArray[np.float64],
    year: int,
    month: int,
    day: int,
    local_time: float,
    required_height: NDArray[np.float64],
    canopy_height: NDArray[np.float64],
    plant_area_index_profile: NDArray[np.float64],
    leaf_orientation_coefficient: float,
    leaf_reluctance_shortwave: float,
    leaf_transmittance_shortwave: float,
    leaf_reluctance_shortwave_par: float,
    leaf_transmittance_shortwave_par: float,
    clumping_factor: float,
    ground_reflectance: float,
    slope: NDArray[np.float64],
    aspect: NDArray[np.float64],
    shortwave_radiation_down: NDArray[np.float64],
    diffuse_radiation_down: NDArray[np.float64],
):
    """Calculate shortwavre radiation below canopy, small leaf model.

    TODO to numpy
    TODO avoid division by zero
    TODO reverse order
    TODO some of the parameters might be plant community and grid cell specific
    TODO check the other functions, there seems to be a lot of repetition, break out
    TODO add test

    """
    # Create output variables
    n_layers = len(plant_area_index_profile)
    absorbed_shortwave_radiation = np.zeros(n_layers)
    par = np.zeros(n_layers)
    downward_direct = np.zeros(n_layers)
    downward_diffuse = np.zeros(n_layers)
    upward_diffuse = np.zeros(n_layers)

    if shortwave_radiation_down > 0:
        # Calculate heights and cumulative plant area index
        mindif = canopy_height
        whichz = 0
        z = np.zeros(n_layers)
        paic = np.zeros(n_layers)
        paic[0] = plant_area_index_profile[0]
        nn = n_layers
        z[0] = (1 / nn) * canopy_height

        for i in range(1, n_layers):
            z[i] = ((i + 1) / nn) * canopy_height
            paic[i] = paic[i - 1] + plant_area_index_profile[i]
            newdif = abs(z[i] - required_height)
            if newdif < mindif:
                whichz = i
                mindif = newdif

        z[whichz] = required_height

        # Calculate and adjust plant area index, TODO note inverted order of layers
        adjusted_plant_area_index = paic[-1] / (1 - clumping_factor)

        # Calculate additional variables
        scattering_albedo = leaf_reluctance_shortwave + leaf_transmittance_shortwave
        scatter_absorption_coefficient = 1 - scattering_albedo
        delta_reflectance_transmittance = (
            leaf_reluctance_shortwave - leaf_transmittance_shortwave
        )

        # Calculate mean_inclination_angle where leaf orientation coefficient not = 1.0
        mean_inclination_angle_full = np.where(
            leaf_orientation_coefficient != 1.0,
            9.65 * np.power((3 + leaf_orientation_coefficient), -1.65),
            1.0 / 3.0,  # note: value from micropoint
        )

        # Clip mean_inclination_angle values to be at most π/2
        mean_inclination_angle = np.minimum(mean_inclination_angle_full, np.pi / 2)

        # Calculate inclination distribution
        inclination_distribution = np.cos(mean_inclination_angle) ** 2

        backward_scattering_coefficient = 0.5 * (
            scattering_albedo
            + inclination_distribution * delta_reflectance_transmittance
        )
        diffuse_scattering_coefficient = np.sqrt(
            scatter_absorption_coefficient**2
            + 2 * scatter_absorption_coefficient * backward_scattering_coefficient
        )

        # Calculate additional variables for PAR
        scattering_albedo_par = (
            leaf_reluctance_shortwave_par + leaf_transmittance_shortwave_par
        )
        scatter_absorption_coefficient_par = 1 - scattering_albedo_par
        delta_reflectance_transmittance_par = (
            leaf_reluctance_shortwave_par - leaf_transmittance_shortwave_par
        )

        backward_scattering_coefficient_par = 0.5 * (
            scattering_albedo_par
            + inclination_distribution * delta_reflectance_transmittance_par
        )
        diffuse_scattering_coefficient_par = np.sqrt(
            scatter_absorption_coefficient_par**2
            + 2
            * scatter_absorption_coefficient_par
            * backward_scattering_coefficient_par
        )

        # Calculate solar position
        solar_position = calculate_solar_position(
            latitude=latitude,
            longitude=longitude,
            year=year,
            month=month,
            day=day,
            local_time=local_time,
        )
        zenith, azimuth = solar_position
        solar_index = calculate_solar_index(
            slope=slope, aspect=aspect, zenith=zenith, azimuth=azimuth
        )
        zenith = min(zenith, 90.0)

        # Calculate two-stream parameters (diffuse)
        diffuse_radiation_parameters = calculate_diffuse_radiation_parameters(
            adjusted_plant_area_index=adjusted_plant_area_index,
            scatter_absorption_coefficient=scatter_absorption_coefficient,
            backward_scattering_coefficient=backward_scattering_coefficient,
            diffuse_scattering_coefficient=diffuse_scattering_coefficient,
            ground_reflectance=ground_reflectance,
        )

        diffuse_radiation_parameters_par = calculate_diffuse_radiation_parameters(
            adjusted_plant_area_index=adjusted_plant_area_index,
            scatter_absorption_coefficient=scatter_absorption_coefficient_par,
            backward_scattering_coefficient=backward_scattering_coefficient_par,
            diffuse_scattering_coefficient=diffuse_scattering_coefficient_par,
            ground_reflectance=ground_reflectance,
        )

        # Canopy extinction coefficient
        kp = calculate_canopy_extinction_coefficients(
            solar_zenith_angle=zenith,
            leaf_inclination_angle_coefficient=leaf_orientation_coefficient,
            solar_index=solar_index,
        )
        k, kd, k0 = kp[0], kp[1], kp[2]
        kc = kd / k0

        # Calculate two-stream parameters (direct)
        sigma = (
            kd**2
            + backward_scattering_coefficient**2
            - (scatter_absorption_coefficient + backward_scattering_coefficient) ** 2
        )
        sigma_par = (
            kd**2
            + backward_scattering_coefficient_par**2
            - (scatter_absorption_coefficient_par + backward_scattering_coefficient_par)
            ** 2
        )

        direct_radiation_parameters = calculate_direct_radiation_parameters(
            adjusted_plant_area_index=adjusted_plant_area_index,
            scattering_albedo=scattering_albedo,
            scatter_absorption_coefficient=scatter_absorption_coefficient,
            backward_scattering_coefficient=backward_scattering_coefficient,
            diffuse_scattering_coefficient=diffuse_scattering_coefficient,
            ground_reflectance=ground_reflectance,
            inclination_distribution=inclination_distribution,
            delta_reflectance_transmittance=delta_reflectance_transmittance,
            extinction_coefficient_k=k,
            extinction_coefficient_kd=kd,
            sigma=sigma,
        )
        direct_radiation_parameters_par = calculate_direct_radiation_parameters(
            adjusted_plant_area_index,
            scattering_albedo_par,
            scatter_absorption_coefficient_par,
            backward_scattering_coefficient_par,
            diffuse_scattering_coefficient=diffuse_scattering_coefficient_par,
            ground_reflectance=ground_reflectance,
            inclination_distribution=inclination_distribution,
            delta_reflectance_transmittance=delta_reflectance_transmittance_par,
            extinction_coefficient_k=k,
            extinction_coefficient_kd=kd,
            sigma=sigma_par,
        )

        # Direct beam above canopy
        direct_beam_above_canopy = (
            shortwave_radiation_down - diffuse_radiation_down
        ) / np.cos(zenith * np.pi / 180)

        # Extract two-stream parameters
        p1, p2, p3, p4 = diffuse_radiation_parameters
        p5, p6, p7, p8, p9, p10 = direct_radiation_parameters
        p1_par, p2_par, p3_par, p4_par = diffuse_radiation_parameters_par
        p5_par, p6_par, p7_par, p8_par, p9_par, p10_par = (
            direct_radiation_parameters_par
        )

        # Iterate through to calculate radiation for each canopy element
        for i in range(n_layers):
            paia = adjusted_plant_area_index - paic[i]
            # Adjust for clumping factor
            n = (canopy_height - z[i]) / canopy_height
            n = max(n, 1 / (nn * 2))
            paia /= 1 - clumping_factor * n
            # transmission through canopy gaps (direct)
            direct_transmission_gaps = clumping_factor ** (kc * n)
            # transmission through canopy gaps (diffuse)
            diffuse_transmission_gaps = clumping_factor ** (2 * n)

            # Shortwave contributions
            # Contribution of direct to downward diffuse
            contribution_direct_to_downward_diffuse = (
                (1 - direct_transmission_gaps)
                * (
                    (p8 / sigma) * np.exp(-kd * paia)
                    + p9 * np.exp(-diffuse_scattering_coefficient * paia)
                    + p10 * np.exp(diffuse_scattering_coefficient * paia)
                )
                + direct_transmission_gaps
            ) * direct_beam_above_canopy
            contribution_direct_to_downward_diffuse = max(
                0,
                min(contribution_direct_to_downward_diffuse, direct_beam_above_canopy),
            )

            #  Contribution of direct to upward diffuse
            contribution_direct_to_upward_diffuse = (
                (1 - direct_transmission_gaps)
                * (
                    (p5 / sigma) * np.exp(-kd * paia)
                    + p6 * np.exp(-diffuse_scattering_coefficient * paia)
                    + p7 * np.exp(diffuse_scattering_coefficient * paia)
                )
            ) * direct_beam_above_canopy
            contribution_direct_to_upward_diffuse = max(
                0, min(contribution_direct_to_upward_diffuse, direct_beam_above_canopy)
            )

            # Downward diffuse
            downward_diffuse[i] = (
                (1 - diffuse_transmission_gaps)
                * (
                    p3 * np.exp(-diffuse_scattering_coefficient * paia)
                    + p4 * np.exp(diffuse_scattering_coefficient * paia)
                )
                + diffuse_transmission_gaps
            ) * diffuse_radiation_down + contribution_direct_to_downward_diffuse

            # Upward diffuse
            upward_diffuse[i] = (
                (1 - diffuse_transmission_gaps)
                * (
                    p1 * np.exp(-diffuse_scattering_coefficient * paia)
                    + p2 * np.exp(diffuse_scattering_coefficient * paia)
                )
                + diffuse_transmission_gaps
            ) * diffuse_radiation_down + contribution_direct_to_upward_diffuse

            # Downward direct
            downward_direct[i] = (
                (1 - direct_transmission_gaps) * (np.exp(-kd * paia))
                + direct_transmission_gaps
            ) * direct_beam_above_canopy

            # Absorbed shortwave radiation
            sil = k * np.cos(zenith * np.pi / 180)
            swupper = (1 - leaf_reluctance_shortwave) * (
                downward_diffuse[i] + sil * downward_direct[i]
            )
            swunder = (1 - leaf_reluctance_shortwave) * upward_diffuse[i]
            absorbed_shortwave_radiation[i] = 0.5 * (swupper + swunder)

            # PAR contributions
            contribution_direct_to_downward_diffuse_par = (
                (1 - direct_transmission_gaps)
                * (
                    (p8_par / sigma_par) * np.exp(-kd * paia)
                    + p9_par * np.exp(-diffuse_scattering_coefficient_par * paia)
                    + p10_par * np.exp(diffuse_scattering_coefficient_par * paia)
                )
                + direct_transmission_gaps
            ) * direct_beam_above_canopy
            contribution_direct_to_downward_diffuse_par = max(
                0,
                min(
                    contribution_direct_to_downward_diffuse_par,
                    direct_beam_above_canopy,
                ),
            )

            contribution_direct_to_upward_diffuse_par = (
                (1 - direct_transmission_gaps)
                * (
                    (p5_par / sigma_par) * np.exp(-kd * paia)
                    + p6_par * np.exp(-diffuse_scattering_coefficient_par * paia)
                    + p7_par * np.exp(diffuse_scattering_coefficient_par * paia)
                )
            ) * direct_beam_above_canopy
            contribution_direct_to_upward_diffuse_par = max(
                0,
                min(
                    contribution_direct_to_upward_diffuse_par, direct_beam_above_canopy
                ),
            )

            # Downward diffuse
            downward_diffuse_par = (
                (1 - diffuse_transmission_gaps)
                * (
                    p3_par * np.exp(-diffuse_scattering_coefficient_par * paia)
                    + p4_par * np.exp(diffuse_scattering_coefficient_par * paia)
                )
                + diffuse_transmission_gaps
            ) * diffuse_radiation_down + contribution_direct_to_downward_diffuse_par

            # Upward diffuse
            upward_diffuse_par = (
                (1 - diffuse_transmission_gaps)
                * (
                    p1_par * np.exp(-diffuse_scattering_coefficient_par * paia)
                    + p2_par * np.exp(diffuse_scattering_coefficient_par * paia)
                )
                + diffuse_transmission_gaps
            ) * diffuse_radiation_down + contribution_direct_to_upward_diffuse_par

            # Absorbed radiation for PAR
            par_upper = (1 - leaf_reluctance_shortwave_par) * (
                downward_diffuse_par + sil * downward_direct[i]
            )
            par_under = (1 - leaf_reluctance_shortwave_par) * upward_diffuse_par
            par[i] = 0.5 * (par_upper + par_under)

    return {
        "absorbed_shortwave_radiation": absorbed_shortwave_radiation,
        "par": par,
        "Rdirdown": downward_direct,
        "diffuse_radiation_downdown": downward_diffuse,
        "shortwave_radiation_up": upward_diffuse,
    }


# from here tested again
def calculate_longwave_radiation_weights(
    plant_area_index_profile: NDArray[np.float64],
) -> dict[str, NDArray[np.float64]]:
    """Calculate weights for longwave radiation through the canopy.

    TODO the order or layers is bottom to top, needs to be

    Args:
        plant_area_index_profile: Plant area index for each canopt layer, [m2 m-2]

    Returns:
        transmission factors (trg, trh) and weights (wgt)
    """

    # Assuming input is a 2D array with shape (n_grid_cells, n_vertical_layers)
    n = plant_area_index_profile.shape[1]  # Number of vertical layers

    # Initialize paib (cumulative PAI across vertical layers) and paia
    paib = np.zeros((plant_area_index_profile.shape[0], n))
    paib[:, 0] = plant_area_index_profile[
        :, 0
    ]  # First vertical layer for each grid cell
    for i in range(1, n):
        paib[:, i] = paib[:, i - 1] + plant_area_index_profile[:, i]

    # pait is the total PAI across all vertical layers for each grid cell
    pait = paib[:, -1]

    # paia is the complement of paib (i.e., total PAI minus cumulative PAI)
    paia = np.zeros_like(paib)
    for i in range(n):
        paia[:, i] = pait - paib[:, i]

    # Initialize transmission matrix tr (n x n for each grid cell)
    tr = np.zeros((plant_area_index_profile.shape[0], n, n))
    for i in range(n):
        for j in range(n):
            pai_diff = np.zeros(plant_area_index_profile.shape[0])
            if i > j:
                pai_diff = paib[:, i] - paib[:, j]
            elif i < j:
                pai_diff = paia[:, i] - paia[:, j]
            tr[:, i, j] = np.exp(-pai_diff)

    # Calculate total weighting from foliage should be
    trg = np.exp(-paib)
    trh = np.exp(-paia)

    # Calculate weights matrix wgt
    wgt = np.zeros_like(tr)
    for i in range(n):
        xx = np.zeros_like(plant_area_index_profile)
        sum_xx = np.zeros(plant_area_index_profile.shape[0])
        for j in range(n):
            xx[:, j] = tr[:, i, j] * plant_area_index_profile[:, j]
            sum_xx += xx[:, j]

        for j in range(n):
            wgt[:, i, j] = xx[:, j] / sum_xx

    return {"trg": trg, "trh": trh, "wgt": wgt}


def calculate_longwave_radiation_below_canopy(
    plant_area_index_profile: NDArray[np.float64],
    longwave_radiation_down: NDArray[np.float64],
    ground_temperature: NDArray[np.float64],
    ground_emissivity: float,
    vegetation_emissivity: float,
    leaf_temperature: NDArray[np.float64],
    stefan_boltzmann_constant: float,
) -> dict[str, NDArray[np.float64]]:
    """Calculate longwave radiation below canopy.

    Args:
        plant_area_index_profile: Plant area index for each canopy layer, [m2 m-2]
        longwave_radiation_down: Longwave downward radiation, [W m-2]
        ground_temperature: Ground temperature, [C]
        ground_emissivity: Ground emissivity, unitless
        vegetation_emissivity: Vegetation emissivity, unitless
        leaf_temperature: Leaf temperature for each canopy layer, [C]
        stefan_boltzmann_constant: Stefan Boltzmann constant

    Returns:
        upward and downward longwave radiation below canopy, [W m-2]
    """

    num_cells, num_layers = plant_area_index_profile.shape
    lwupper = np.zeros((num_cells, num_layers))
    lwunder = np.zeros((num_cells, num_layers))
    # Calculate longwave radiation weights
    wgts = calculate_longwave_radiation_weights(
        plant_area_index_profile=plant_area_index_profile
    )
    for cell in range(num_cells):
        for layer in range(num_layers):
            longwave_sky = longwave_radiation_down[cell] * wgts["trh"][cell, layer]
            longwave_ground = (
                ground_emissivity
                * stefan_boltzmann_constant
                * wgts["trg"][cell, layer]
                * (ground_temperature[cell] + 273.15) ** 4
            )

            smd = np.sum(wgts["wgt"][cell, layer, layer:])  # Sum from layer to n
            smu = np.sum(wgts["wgt"][cell, layer, : layer + 1])  # Sum from 0 to layer

            mua = 1.0 / smd if smd > 0 else 1.0
            mub = 1.0 / smu if smu > 0 else 1.0

            # Calculate weighted longwave radiation for foliage
            lwfd = np.sum(
                wgts["wgt"][cell, layer, layer:]
                * stefan_boltzmann_constant
                * (leaf_temperature[cell, layer:] + 273.15) ** 4
            )
            lwfu = np.sum(
                wgts["wgt"][cell, layer, : layer + 1]
                * stefan_boltzmann_constant
                * (leaf_temperature[cell, : layer + 1] + 273.15) ** 4
            )

            # Aggregate results across layers
            lwupper[cell, layer] += (
                longwave_sky
                + (1 - wgts["trh"][cell, layer]) * lwfd * mua * vegetation_emissivity
            )
            lwunder[cell, layer] += (
                longwave_ground
                + (1 - wgts["trg"][cell, layer]) * lwfu * mub * vegetation_emissivity
            )

    # Average over layers for final output
    lwupper_mean = np.mean(lwupper, axis=1)
    lwunder_mean = np.mean(lwunder, axis=1)

    return {
        "longwave_radiation_down": lwupper_mean,
        "longwave_radiation_up": lwunder_mean,
    }


def calculate_canopy_wind(
    canopy_height: NDArray[np.float64],
    plant_area_index_profile: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate canopy wind.

    Args:
        canopy_height: Canopy height, [m]
        plant_area_index_profile: Vertical profile of plant area index, [m2 m-2]

    Returns:
        wind speed, [m s-1]
    """

    num_cells, num_layers = plant_area_index_profile.shape
    wind_profile = np.ones((num_cells, num_layers))

    for i in range(num_cells):
        # Step 1: Calculate whole canopy attenuation coefficient for this grid cell
        plant_area_index_sum = np.sum(plant_area_index_profile[i, :])
        beta = 0.205 * np.power(plant_area_index_sum, 0.445) + 0.1
        a = plant_area_index_sum / canopy_height[i]
        canopy_factor = np.power(0.25 * a, -1)
        mixing_length = 2 * np.power(beta, 3) * canopy_factor
        attenuation_coefficient = beta * canopy_height[i] / mixing_length

        # Step 2: Calculate attenuation coefficient for each vertical layer in this cell
        attenuation_coefficient_i = np.zeros(num_layers)
        sum_attenuation_coefficient_i = 0
        for j in range(num_layers):
            beta_i = 0.205 * np.power(plant_area_index_profile[i, j], 0.445) + 0.1
            a_i = plant_area_index_profile[i, j] / canopy_height[i]
            canopy_factor_i = np.power(0.25 * a_i, -1)
            mixing_length_i = 2 * np.power(beta_i, 3) * canopy_factor_i
            attenuation_coefficient_i[j] = beta_i * canopy_height[i] / mixing_length_i
            sum_attenuation_coefficient_i += attenuation_coefficient_i[j]

        # Step 3: Adjust attenuation coefficient for this grid cell
        attenuation_coefficient_i /= sum_attenuation_coefficient_i
        attenuation_coefficient_i *= attenuation_coefficient

        # Step 4: Calculate canopy wind shelter coefficient
        n2 = np.trunc(num_layers / 10).astype(int)
        for j in range(num_layers - 1, n2, -1):
            wind_profile[i, j - 1] = wind_profile[i, j] * (
                1 - attenuation_coefficient_i[j - 1]
            )

        # Step 5: Calculate bottom 10% of the wind profile
        roughness_length = canopy_height[i] / (20.0 * n2)
        for j in range(n2):
            z2 = (j + 1) * canopy_height[i] / (10 * n2)
            uf = (0.4 * wind_profile[i, n2 - 1]) / np.log(
                canopy_height[i] / (10 * roughness_length)
            )
            wind_profile[i, j] = (uf / 0.4) * np.log(z2 / roughness_length)

    return wind_profile  # return values need to be transposed i think


# fluxes
# LangrangianOne
