"""The radiation model calculates the radiation balance of the Virtual Ecosystem. This
incluses direct and diffuse radiation components, shortwave and longwave radiation
within the canopy and at the surface. The implementation is based on the 'micropoint'
package, see https://github.com/ilyamaclean/micropoint.

Part of this module will likely be replaced by pyrealm functions in the future to better
integrate with the plant component.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray


# Shortwave radiation
def calculate_julian_day(year: int, month: int, day: int) -> int:
    """Calculate Astronomical Julian day.

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
) -> list[NDArray[np.float64]]:
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
    extinction_coefficient_k = np.where(
        leaf_inclination_angle_coefficient == 1.0,
        1 / (2 * np.cos(zenith_angle_rad)),
        np.where(
            np.isinf(leaf_inclination_angle_coefficient),
            1.0,
            np.sqrt(
                leaf_inclination_angle_coefficient**2 + np.tan(zenith_angle_rad) ** 2
            )
            / (
                leaf_inclination_angle_coefficient
                + 1.774 * (leaf_inclination_angle_coefficient + 1.182) ** -0.733
            ),
        ),
    )

    # Cap extinction coefficient k
    extinction_coefficient_k = np.where(
        extinction_coefficient_k > 6000.0, 6000.0, extinction_coefficient_k
    )

    # Calculate adjusted k0
    extinction_coefficient_k0 = np.where(
        leaf_inclination_angle_coefficient == 1.0,
        0.5,
        np.where(
            np.isinf(leaf_inclination_angle_coefficient),
            1.0,
            np.sqrt(leaf_inclination_angle_coefficient**2)
            / (
                leaf_inclination_angle_coefficient
                + 1.774 * (leaf_inclination_angle_coefficient + 1.182) ** -0.733
            ),
        ),
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
    ground_reflectance: float,  # gref TODO could be array with variable soil types
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
    if ground_reflectance == 0.0:
        ground_reflectance = 0.001

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
) -> list[float | NDArray[np.float64]]:
    """Calculates parameters for direct radiation using two-stream model.

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
    plant_area_index_sum: NDArray[np.float64],
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
    topofcanopy_shortwave_radiation: NDArray[np.float64],
    topofcanopy_diffuse_radiation: NDArray[np.float64],
    leaf_inclination_angle_coefficient: float,
) -> dict[str, NDArray[np.float64]]:
    """Calculate absorbed shortwave radiation for ground and canopy.

    The initial model (micropoint, Maclean) is for a time series and includes a loop.
    Here, only for one time step at the moement.

    Args:
        plant_area_index_sum: Plant area index vertically summed, [m2 m-2]
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
        topofcanopy_shortwave_radiation: Shortwave radiation, [W m-2]
        topofcanopy_diffuse_radiation: Diffuse radiation, [W m-2]
        leaf_inclination_angle_coefficient: Leaf inclination angle coefficient

    Returns:
        dictionary with ground and canopy absorbed radiation and albedo
    """

    absorbed_shortwave_radiation = {}

    # Calculate time-invariant variables
    adjusted_plant_area_index = plant_area_index_sum / (1 - clumping_factor)

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

    # Calculate scattering coefficients
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

    beam_radiation = (
        topofcanopy_shortwave_radiation - topofcanopy_diffuse_radiation
    ) / np.cos(zenith * np.pi / 180)

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
        + diffuse_downward_radiation * topofcanopy_diffuse_radiation
    )

    direct_radiation_ground = (1 - ground_reflectance) * (
        downward_direct_stream * beam_radiation * solar_index
    )

    ground_shortwave_absorption_veg = diffuse_radiation_ground + direct_radiation_ground

    # Radiation absorbed by canopy TODO coordinate with plants model
    diffuse_radiation_canopy = (1 - albedo_diffuse) * topofcanopy_diffuse_radiation
    direct_radiation_canopy = (1 - albedo_beam) * beam_radiation * solar_index
    canopy_shortwave_absorption_veg = diffuse_radiation_canopy + direct_radiation_canopy

    albedo_veg = np.clip(
        1 - (canopy_shortwave_absorption_veg / topofcanopy_shortwave_radiation),
        0.01,
        0.99,
    )

    # where plant area index not >0
    ground_shortwave_absorption_no_veg = (1 - ground_reflectance) * (
        topofcanopy_diffuse_radiation + solar_index * beam_radiation
    )

    ground_shortwave_absorption = np.where(
        plant_area_index_sum > 0,
        ground_shortwave_absorption_veg,
        ground_shortwave_absorption_no_veg,
    )
    canopy_shortwave_absorption = np.where(
        plant_area_index_sum > 0,
        canopy_shortwave_absorption_veg,
        ground_shortwave_absorption_no_veg,
    )
    albedo = np.where(plant_area_index_sum > 0, albedo_veg, ground_reflectance)

    # return values for positive shortwave radiation, else 0.
    absorbed_shortwave_radiation["ground_shortwave_absorption"] = np.where(
        topofcanopy_shortwave_radiation > 0,
        ground_shortwave_absorption,
        0.0,
    ).squeeze()  # TODO for some reason I have extra dimension here
    absorbed_shortwave_radiation["canopy_shortwave_absorption"] = np.where(
        topofcanopy_shortwave_radiation > 0,
        canopy_shortwave_absorption,
        0.0,
    )

    absorbed_shortwave_radiation["albedo"] = np.where(
        topofcanopy_shortwave_radiation > 0, albedo, leaf_reluctance_shortwave
    )

    return absorbed_shortwave_radiation


# longwave radiation
def calculate_canopy_longwave_emission(
    leaf_emissivity: float,
    canopy_temperature: NDArray[np.float64],
    stefan_boltzmann_constant: float,
    zero_Celsius: float,
) -> NDArray[np.float64]:
    """Calculate mean canopy longwave emission.

    Args:
        leaf_emissivity: leaf emissivity, dimensionless
        canopy_temperature: Canopy temperature, [C]
        stefan_boltzmann_constant: Stefan boltzmann constant
        zero_Celsius: Celsius to Kelvin conversion factor

    Returns:
        longwave emission from canopy, [W m-2]
    """

    return (
        leaf_emissivity
        * stefan_boltzmann_constant
        * (np.mean(canopy_temperature, axis=1) + zero_Celsius) ** 4
    )


def calculate_longwave_emission_ground(
    ground_emissivity: float,
    radiation_transmission_coefficient: NDArray[np.float64],
    longwave_downward_radiation_sky: NDArray[np.float64],
    canopy_longwave_emission: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate longwave emission from ground surface.

    Args:
        ground_emissivity: Ground emissivity, dimensionless
        radiation_transmission_coefficient: Radiation transmission coefficient
        longwave_downward_radiation_sky: Longwave downward radiation from sky, [W m-2]
        canopy_longwave_emission: longwave emission from canopy, [W m-2]

    Returns:
        longwave emission from ground surface, [W m-2]
    """
    return ground_emissivity * (
        radiation_transmission_coefficient * longwave_downward_radiation_sky
        + (1 - radiation_transmission_coefficient) * canopy_longwave_emission
    )
