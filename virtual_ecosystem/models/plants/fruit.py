"""This module provides functionality for simulating fruit and seed dynamics."""

import numpy as np
import xarray as xr


def calculate_fallen_fruit_decay_fraction(
    decay_rate: float,
    surface_temperature: xr.DataArray,
    days: int,
    base_temperature: int = 0,
) -> xr.DataArray:
    """Calculate fraction of fallen fruit that decays in a given timestep.

    The fraction of fruit (flesh) that has decayed is effected by two things: the
    length of the simulation time step, and the average (soil surface) temperature
    for this time step. We combine these into a single measure, degree days, relative to
    a base temperature: if temperatures are below that base temperature, then no
    decay will occur.

    Args:
        decay_rate: Rate at which fruit decays [Celsius^-1 day^-1]
        surface_temperature: Temperature of the forest floor [Celsius]
        days: The number of days for elapsed at that temperature [day]
        base_temperature: The reference temperature above which decay occurs [Celsius]

    Returns:
        The fraction of the fallen fruit that has decayed into the soil.
    """

    # Calculate the degree days (subzero temperatures are treated as zero)
    degree_days = xr.where(
        surface_temperature >= base_temperature,
        (surface_temperature - base_temperature) * days,
        0.0,
    )

    return 1 - np.exp(-decay_rate * degree_days)
