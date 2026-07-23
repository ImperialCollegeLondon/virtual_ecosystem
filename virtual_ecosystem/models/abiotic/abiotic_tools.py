"""The ``models.abiotic.abiotic_tools`` module contains a set of general functions that
are shared across submodules in the
:mod:`~virtual_ecosystem.models.abiotic.abiotic_model` model.

TODO cross-check with pyrealm for duplication/ different implementation
TODO change temperatures to Kelvin
"""  # noqa: D205

from collections.abc import Iterable
from types import SimpleNamespace

import bottleneck as bn
import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calc_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic.wind import next_valid_below


def build_indices(data: Data, layer_structure: LayerStructure) -> SimpleNamespace:
    """Build indices for different layers and variables for easier access.

    Args:
        data: Data object
        layer_structure: Layer structure object

    Returns:
        SimpleNamespace with indices for different layers and variables
    """

    return SimpleNamespace(
        above=layer_structure.index_above,
        canopy=layer_structure.index_filled_canopy,
        surface=layer_structure.index_surface_scalar,
        atm=layer_structure.index_filled_atmosphere,
        flux=layer_structure.index_flux_layers,
        soil=layer_structure.index_all_soil,
        topsoil=layer_structure.index_topsoil_scalar,
        layers=layer_structure.n_layers,
        cell_id=data.grid.n_cells,
    )


def calculate_molar_density_air(
    temperature: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    standard_mole: float,
    standard_pressure: float,
    celsius_to_kelvin: float,
) -> NDArray[np.floating]:
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


def calculate_air_density(
    air_temperature: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    specific_gas_constant_dry_air: float,
    celsius_to_kelvin: float,
):
    """Calculate the density of air using the ideal gas law.

    Args:
        air_temperature: Air temperature, [C]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        specific_gas_constant_dry_air: Specific gas constant for dry air, [J kg-1 K-1]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin

    Returns:
        density of air, [kg m-3].
    """
    # Convert temperature from Celsius to Kelvin
    temperature_k = air_temperature + celsius_to_kelvin

    # Calculate density using the ideal gas law
    return (
        atmospheric_pressure * 1000.0 / (temperature_k * specific_gas_constant_dry_air)
    )


def calculate_latent_heat_vapourisation(
    temperature: NDArray[np.floating],
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factors: tuple[float, float],
) -> NDArray[np.floating]:
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
    a, b = latent_heat_vap_equ_factors
    return (a * (temperature_kelvin / (temperature_kelvin - b)) ** 2) / 1000.0


def find_last_valid_row(array: NDArray[np.floating]) -> NDArray[np.floating]:
    """Find last valid value in array for each column.

    This function looks for the last valid value in each column of a 2-dimensional
    array. If the previous value is nan, it moved up the array. If all values are NaN,
    the value is set to NaN, too.

    Args:
        array: Two-dimesional array for which last valid values should be found

    Returns:
        Array that contains last valid values
    """
    # Initialize an empty list to store the last valid value from each column
    new_row = []

    # Loop through each column
    for column in range(array.shape[1]):
        # Scan from the last row to the first in the current column
        for i in range(array.shape[0] - 1, -1, -1):
            if not np.isnan(array[i, column]):
                # Append the last valid value found in the column to the new_row list
                new_row.append(array[i, column])
                break
        else:
            # If no valid value is found in the column, append NaN
            new_row.append(np.nan)

    return np.array(new_row)


def calculate_slope_of_saturated_pressure_curve(
    temperature: NDArray[np.floating],
    saturated_pressure_slope_parameters: tuple[float, float, float, float],
) -> NDArray[np.floating]:
    r"""Calculate slope of the saturated pressure curve.

    Args:
        temperature: Temperature, [C]
        saturated_pressure_slope_parameters: List of parameters to calculate
            the slope of the saturated vapour pressure curve

    Returns:
        Slope of the saturated pressure curve, :math:`\Delta_{v}`
    """

    a, b, c, d = saturated_pressure_slope_parameters
    return (
        a * (b * np.exp(c * temperature / (temperature + d))) / (temperature + d) ** 2
    )


def calculate_actual_vapour_pressure(
    air_temperature: DataArray,
    relative_humidity: DataArray,
    pyrealm_core_constants: PyrealmCoreConst,
) -> DataArray:
    """Calculate actual vapour pressure, [kPa].

    Args:
        air_temperature: Air temperature, [C]
        relative_humidity: Relative humidity, [-]
        pyrealm_core_constants: Set of constants from pyrealm

    Returns:
        actual vapour pressure, [kPa]
    """

    saturation_vapour_pressure_air = calc_vp_sat(
        ta=air_temperature.to_numpy(),
        core_const=pyrealm_core_constants,
    )
    return saturation_vapour_pressure_air * relative_humidity / 100.0


def set_unintended_nan_to_zero(
    input_array: NDArray[np.floating],
    input_nan_mask: NDArray[np.bool],
) -> NDArray[np.floating]:
    """Clean up outputs: set unintended NaNs to 0, preserve intended NaNs.

    Args:
        input_array: Input array that may contain NaN
        input_nan_mask: A mask of intended NaN

    Returns:
        Array with unintended NaN set to zero
    """
    arr_clean = np.where(np.isnan(input_array), 0.0, input_array)
    arr_clean[input_nan_mask] = np.nan
    return arr_clean


def compute_layer_thickness_for_varying_canopy(
    heights: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Calculate layer thickness for varying canopy layers, true layers only.

    Calculate layer thickness by subtracting from the next valid layer below (skipping
    NaNs), and for the last valid layer in each column subtract from zero (ground
    level).


    Args:
        heights: 2D array of layer heights, [m]

    Returns:
        2D array of layer thickness, [m], same shape as input
    """

    # Fill np.nan values from the bottom up along the 0 axis
    nan_filled_heights = np.flipud(bn.push(np.flipud(heights), axis=0))

    # Find the differences down through the canopy to the surface and swap sign
    canopy_thickness = -np.diff(nan_filled_heights, axis=0)

    # Add the surface layer heights down to zero
    thickness = np.concat([canopy_thickness, heights[[-1], :]])

    # Mask out the filled layers - should all be zero and match the original np.nans
    thickness = np.where(np.isnan(heights), np.nan, thickness)

    return thickness


def compute_aboveground_layer_thickness(
    heights: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Calculate layer thickness for above ground layers only.

    Calculate layer thickness by subtracting from the next valid layer below (skipping
    NaNs), and for the last valid layer in each column subtract from zero (ground
    level). Soil layers are set to NaN.


    Args:
        heights: 2D array of layer heights, [m]

    Returns:
        2D array of layer thickness, [m], same shape as input
    """

    n_layers, n_cols = heights.shape

    thickness = np.full_like(heights, np.nan)

    # only above ground
    above_ground = heights > 0
    valid = above_ground & ~np.isnan(heights)

    # next valid below above ground
    above_ground_heights = np.where(above_ground, heights, np.nan)
    below_idx = next_valid_below(above_ground_heights)

    cols = np.broadcast_to(np.arange(n_cols), (n_layers, n_cols))

    mask = valid & (below_idx >= 0)

    h_top = heights[mask]
    h_bot = heights[below_idx[mask], cols[mask]]

    thickness[mask] = np.abs(h_top - h_bot)

    # last above ground layer → ground
    mask_last = valid & (below_idx < 0)
    thickness[mask_last] = np.abs(heights[mask_last])
    return thickness


def calculate_specific_humidity(
    air_temperature: NDArray[np.floating],
    relative_humidity: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    molecular_weight_ratio_water_to_dry_air: float,
    pyrealm_core_constants: PyrealmCoreConst,
) -> NDArray[np.floating]:
    """Calculate specific humidity.

    Args:
        air_temperature: Air temperature, [C]
        relative_humidity: Relative humidity, [%]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        molecular_weight_ratio_water_to_dry_air: The ratio of the molar mass of water
            vapour to the molar mass of dry air
        pyrealm_core_constants: Pyrealm core constants

    Returns:
        Specific humidity, [kg kg-1]
    """
    # Saturation vapor pressure
    saturation_vapour_pressure = calc_vp_sat(
        ta=air_temperature,
        core_const=pyrealm_core_constants,
    )

    # Actual vapor pressure (hPa)
    actual_vapour_pressure = (relative_humidity / 100.0) * saturation_vapour_pressure

    # Specific humidity formula
    specific_humidity = (
        molecular_weight_ratio_water_to_dry_air * actual_vapour_pressure
    ) / (
        atmospheric_pressure
        - ((1 - molecular_weight_ratio_water_to_dry_air) * actual_vapour_pressure)
    )

    return specific_humidity


def update_profile_from_reference(
    layer_structure: LayerStructure,
    mask_variable: DataArray,
    variable_name: DataArray,
    time_index: int,
) -> DataArray:
    """Update a layer-based profile for a given time index using a reference variable.

    This function

      - extracts a mask from air temperature to determine valid atmosphere layers
      - reads the reference variable at the given time index
      - applies the mask to keep only valid layers
      - fills the profile template for those layers

    Args:
        layer_structure: LayerStructure object defining the layer setup
        mask_variable: DataArray used to create the atmospheric mask
        variable_name: Reference variable (e.g. data["atmospheric_pressure_ref"])
        time_index: Index of the current time step

    Returns:
        Updated layer profile as a DataArray
    """

    # Create atmospheric mask for filling constant values
    atm_mask = ~np.isnan(
        mask_variable.isel(layers=layer_structure.index_filled_atmosphere)
    )

    # Mean atmospheric pressure profile, [kPa]
    profile_out = layer_structure.from_template()
    reference_values = variable_name.isel(time_index=time_index)
    valid_values = reference_values.where(atm_mask)
    profile_out[layer_structure.index_filled_atmosphere] = valid_values

    return profile_out


def calculate_atmospheric_layer_geometry(
    data: Data, idx: SimpleNamespace, minimum_mixing_depth: float
) -> dict[str, NDArray[np.floating]]:
    """Calculate heights, layer thickness, and midpoints for atmospheric layers.

    The midpoint values are distances in metres above ground for each cell.
    For layer heights below the surface layer, a minimum mixing depth is introduced.
    This is to prevent unrealistically low mixing depths and therefore high temperatures
    in the lowest canopy layer when the layer height is very low. Note that this is an
    artificial inflation of the mixing depth.

    Args:
        data: Data object
        idx: SimpleNamespace containing layer indices
        minimum_mixing_depth: Minimum depth for lowest canopy layer, [m]

    Returns:
        dict containing heights, thickness, layer_top, layer_midpoints
    """

    # Extract above-ground layer heights and correct of lowest canopy layer is below
    # surface layer height
    heights = data["layer_heights"].to_numpy().copy()

    # Set minimum mixing depth
    heights[idx.canopy] = np.where(
        heights[idx.canopy] <= minimum_mixing_depth,
        minimum_mixing_depth,
        heights[idx.canopy],
    )
    heights_corrected = np.where(
        np.isnan(data["layer_heights"].to_numpy()), np.nan, heights
    )

    # Compute thickness
    thickness = compute_aboveground_layer_thickness(heights=heights_corrected)

    # Compute the midpoint of each layer as the height above ground minus half the layer
    # thickness
    midpoints = heights_corrected - thickness / 2

    return {
        "heights": heights,
        "thickness": thickness,
        "layer_midpoints": midpoints,
    }


def generate_diurnal_cycle_from_monthly_data(
    monthly_air_temperature: NDArray[np.floating],
    monthly_shortwave_absorption: NDArray[np.floating],
    monthly_relative_humidity: NDArray[np.floating],
    monthly_evapotranspiration: NDArray[np.floating],
    monthly_soil_evaporation: NDArray[np.floating],
    daily_temp_amplitude: NDArray[np.floating],
    latitude_deg: float,
    month: int,
    days: int,
) -> dict[str, NDArray[np.floating]]:
    """Generate synthetic hourly forcing for one day from monthly averages.

    Args:
        monthly_air_temperature: Monthly mean air temperature [C]
        monthly_shortwave_absorption: Monthly mean daily shortwave absorption [W m-2]
        monthly_relative_humidity: Monthly mean relative humidity [%]
        monthly_evapotranspiration: Monthly total evapotranspiration [mm/month]
        monthly_soil_evaporation: Monthly total soil evaporation [mm/month]
        daily_temp_amplitude: typical diurnal temperature swing [C]
        latitude_deg: Latitude for daylength calculation [deg]
        month: Month number [1-12]
        days: Number of days in month


    Returns:
        dict of arrays air_temperature_hourly, shortwave_absorption_hourly,
        relative_humidity_hourly, evapotranspiration_hourly, soil_evaporation_hourly
    """

    hours_per_day = 24
    hours = np.arange(hours_per_day)

    # Air temperature (sine wave, max at 14:00), (hours_per_day, cell)
    air_temperature_hourly = monthly_air_temperature[
        None, :
    ] + daily_temp_amplitude * np.sin(2 * np.pi * (hours[:, None] - 8) / hours_per_day)

    # Daylength (simple climatology)
    daylength = 12 + 4 * np.cos((month - 1) * np.pi / 6) * np.cos(
        np.radians(latitude_deg)
    )
    daylength = np.clip(daylength, 6.0, 18.0)

    sunrise = 12 - daylength / 2
    sunset = 12 + daylength / 2

    # Shortwave radiation (half-sine over daylight), shape (hours_per_day,)
    hour_fraction = np.zeros(hours_per_day)
    for h in range(hours_per_day):
        if sunrise <= h <= sunset:
            hour_fraction[h] = np.sin(np.pi * (h - sunrise) / daylength)

    # Normalise so daytime hours sum to 1 — night hours remain 0
    if hour_fraction.sum() > 0:
        hour_fraction /= hour_fraction.sum()

    # Shortwave absorption (hours_per_day, layer, cell)
    shortwave_absorption_hourly = (
        monthly_shortwave_absorption[None, :, :] * hour_fraction[:, None, None]
    )

    # Relative humidity (constant vapour pressure approach)
    e_s_mean = calc_vp_sat(monthly_air_temperature)
    e_a = monthly_relative_humidity / 100.0 * e_s_mean
    e_s_hourly = calc_vp_sat(air_temperature_hourly)
    relative_humidity_hourly = np.clip(100.0 * e_a[None, :] / e_s_hourly, 0.0, 100.0)

    # Evapotranspiration — conserve monthly total, distribute by radiation.
    # hour_fraction is already normalised to sum=1 over daytime hours and
    # is 0 at night, so multiplying by it gives zero ET at night AND
    # preserves the daily total exactly.
    #
    # Shape: (hours_per_day, layer, cell)
    monthly_et = monthly_evapotranspiration[None, :, :]  # (1, layer, cell)
    daily_et = monthly_et / days  # (1, layer, cell)

    # Distribute daily ET by hour_fraction (zero at night, sums to 1 over day)
    evapotranspiration_hourly = daily_et * hour_fraction[:, None, None]

    # Preserve NaN structure from input (unoccupied canopy layers)
    canopy_nan_mask = np.isnan(monthly_evapotranspiration)  # (layer, cell)
    evapotranspiration_hourly = np.where(
        canopy_nan_mask[None, :, :],
        np.nan,
        evapotranspiration_hourly,
    )

    # Soil evaporation — same approach, shape (hours_per_day, cell)
    monthly_soil = monthly_soil_evaporation[None, :]  # (1, cell)
    daily_soil = monthly_soil / days  # (1, cell)

    soil_evaporation_hourly = daily_soil * hour_fraction[:, None]

    # Preserve NaN structure from input
    soil_nan_mask = np.isnan(monthly_soil_evaporation)  # (cell,)
    soil_evaporation_hourly = np.where(
        soil_nan_mask[None, :],
        np.nan,
        soil_evaporation_hourly,
    )

    return {
        "air_temperature_hourly": air_temperature_hourly,
        "relative_humidity_hourly": relative_humidity_hourly,
        "shortwave_absorption_hourly": shortwave_absorption_hourly,
        "evapotranspiration_hourly": evapotranspiration_hourly,
        "soil_evaporation_hourly": soil_evaporation_hourly,
    }


def fill_layer_template(
    layer_structure: LayerStructure,
    assignments: list[tuple],
) -> NDArray[np.floating]:
    """Fill layer template with index values.

    Args:
        layer_structure: LayerStructure
        assignments: list of variable names, indices and values

    Returns:
        array with updated indices
    """
    out = layer_structure.from_template().to_numpy()

    for indices, values in assignments:
        out[indices, :] = values

    return out


def record_hourly_output(
    hour: int,
    data_record: dict,
    hourly_values: dict,
):
    """Record hourly data.

    Args:
        hour: Hour of the day
        data_record: dict that contains all hourly data
        hourly_values: Hourly values

    Returns:
        updated dict with hour values
    """

    # Assign values to data_record
    for var, value in hourly_values.items():
        if var not in data_record:
            continue

        else:
            data_record[var][hour] = value
    return data_record


def mean_to_layers(
    var: str, index: list[int], data_record: dict, layer_structure: LayerStructure
) -> DataArray:
    """Return mean value over time for given variable and fill into layer structure.

    Args:
        var: Variable name
        index: List of layer indices to fill
        data_record: Data record dict
        layer_structure: LayerStructure object

    Returns:
        DataArray with mean values filled into layer structure
    """
    out = layer_structure.from_template()
    mean_vals = np.nanmean(data_record[var], axis=0)
    out[index] = mean_vals[index]
    return out


def initialize_data_record(
    variables: dict[str, DataArray],
    time_dim: int,
    layers: int,
    cell_ids: int,
) -> dict[str, NDArray[np.floating]]:
    """Create a data_record dict with a new leading time dimension.

    Assumptions are that 1D variables have shape (cell_ids,) and 2D variables have shape
    (layers, cell_ids).

    Args:
        variables : Dictionary of variable names to template arrays
        time_dim : Size of the new time dimension (e.g. 24)
        layers : Number of layers
        cell_ids : Number of cell ids

    Returns:
        Dictionary with initialized arrays filled with NaNs.

    Raises:
        ValueError: is number of dimensions cannot be matched
    """
    data_record = {}

    for var, arr in variables.items():
        shape: tuple[int, ...]

        if arr.ndim == 1:
            shape = (time_dim, cell_ids)
        elif arr.ndim == 2:
            shape = (time_dim, layers, cell_ids)
        else:
            raise ValueError(
                f"Unsupported number of dimensions for '{var}': {arr.ndim}"
            )

        data_record[var] = np.full(shape, np.nan)

    return data_record


def validate_variables(
    names: tuple[str, ...],
    values: dict[str, object],
    exclude: Iterable[str] = (),
) -> None:
    """Validate all variables are in update dictionary.

    Args:
        names: variable names in output
        values: variables in hourly update
        exclude: variable names to ignore in the comparison

    Returns:
        None

    Raises:
        ValueError: if variable mismatch is detected.
    """
    exclude_set = set(exclude)

    names_set = set(names) - exclude_set
    values_set = set(values) - exclude_set

    missing = names_set - values_set
    extra = values_set - names_set

    if missing or extra:
        raise ValueError(
            "Variable mismatch detected\n"
            f"Missing: {sorted(missing)}\n"
            f"Extra: {sorted(extra)}"
        )


def finite_and_within(arr: DataArray, low: float, high: float, name: str) -> None:
    """Test that values are finite and within bounds.

    Args:
        arr: Output DataArray to be tested
        low: Minimum value
        high: maximum value
        name: name of variable

    Returns:
        None.

    Raises:
        AssertionError: if values are not finite or outside bounds.

    """

    values = np.asarray(arr)

    finite = np.isfinite(values)
    assert finite.any(), f"{name} has no finite values"

    # ignore NaNs
    min_val = np.nanmin(values)
    max_val = np.nanmax(values)

    assert min_val >= low, f"{name} below {low}"
    assert max_val <= high, f"{name} above {high}"


def compute_weights_from_absorbed_radiation(
    radiation: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Convert a 2D radiation array into normalized weights that sum to 1.

    Weights sum to 1 along the layer axis (axis=0) for each cell independently,
    ignoring NaN values. NaN entries in the input remain NaN in the output.
    Cells where all valid radiation is zero return NaN weights — these are cells
    with no canopy and no radiation to distribute.

    Args:
        radiation: 2D array of absorbed radiation values for each layer and cell

    Returns:
        2D array of normalized weights corresponding to the absorbed radiation
    """
    # Sum over layers per cell, ignoring NaNs, keep dims for broadcasting
    total = np.nansum(radiation, axis=0, keepdims=True)  # shape (1, cells)

    # Where total is zero, set to NaN so division produces NaN instead of inf
    # This handles no-canopy cells cleanly without raising
    safe_total = np.where(total == 0.0, np.nan, total)

    # Divide — NaN entries stay NaN, zero-total cells become NaN
    return radiation / safe_total
