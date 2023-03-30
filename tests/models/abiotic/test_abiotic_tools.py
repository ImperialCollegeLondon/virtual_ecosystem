"""Test abiotic_tools.py."""

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in abiotic tools tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.abiotic.abiotic_tools import set_layers_function

    # Setup the data object with two cells.
    grid = Grid(cell_nx=3, cell_ny=1)
    data = Data(grid)

    # define layers along coordinates
    # TODO from abiotic_model
    layers_function = set_layers_function(canopy_layers=3, soil_layers=1)

    # Add the required data.
    data["temperature_2m"] = DataArray(
        [[30, 20, 30]],
        dims=["layers", "cell_id"],
        coords={
            "layers": [len(layers_function) - 1],
            "layers_function": ("layers", [layers_function[-1]]),
            "cell_id": [0, 1, 2],
        },
    )
    data["air_temperature"] = DataArray(
        [
            [22, 22, 22],
            [24, 24, 24],
            [26, 26, 26],
            [28, 28, 28],
            [30, 30, 30],
            [32, 32, 32],
        ],
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(1, (len(layers_function))),
            "layers_function": (
                "layers",
                layers_function[1 : (len(layers_function))],
            ),
            "cell_id": [0, 1, 2],
        },
    )
    data["wind_below_canopy"] = DataArray(
        [[0.1, 0.1, 0.1], [1, 0.5, 0.5], [2, 2, 5], [3, 4, 10], [5, 7, 12]],
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(1, (len(layers_function) - 1)),
            "layers_function": (
                "layers",
                layers_function[1 : (len(layers_function) - 1)],
            ),
            "cell_id": [0, 1, 2],
        },
    )

    data["atmospheric_pressure"] = DataArray(
        [[101, 102, 103]],
        dims=["layers", "cell_id"],
        coords={
            "layers": [len(layers_function) - 1],
            "layers_function": ("layers", [layers_function[-1]]),
            "cell_id": [0, 1, 2],
        },
    )

    return data


def test_calc_molar_density_air(dummy_data):
    """Test calculate molar desity of air."""

    from virtual_rainforest.models.abiotic import abiotic_tools

    data = dummy_data
    layers_function = abiotic_tools.set_layers_function(canopy_layers=3, soil_layers=1)

    result = abiotic_tools.calc_molar_density_air(
        temperature=data["temperature_2m"],
        atmospheric_pressure=data["atmospheric_pressure"],
    )
    xr.testing.assert_allclose(
        result,
        DataArray(
            [[120.618713, 119.436176, 118.276602]],
            dims=["layers", "cell_id"],
            coords={
                "layers": [len(layers_function) - 1],
                "layers_function": ("layers", ["above"]),
                "cell_id": [0, 1, 2],
            },
            name="molar_density_air",
        ),
    )


def test_calc_specific_heat_air(dummy_data):
    """Test calculate specific heat of air."""

    from virtual_rainforest.models.abiotic import abiotic_tools

    data = dummy_data
    layers_function = abiotic_tools.set_layers_function(canopy_layers=3, soil_layers=1)

    result = abiotic_tools.calc_specific_heat_air(temperature=data["temperature_2m"])

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[29.214, 29.202, 29.214]],
            dims=["layers", "cell_id"],
            coords={
                "layers": [len(layers_function) - 1],
                "layers_function": ("layers", [layers_function[-1]]),
                "cell_id": [0, 1, 2],
            },
            name="specific_heat_air",
        ),
    )


def test_calculate_latent_heat_vaporisation(dummy_data):
    """Test.

    TODO check why it does not work with dummy_data.
    """

    from virtual_rainforest.models.abiotic import abiotic_tools

    data = dummy_data
    layers_function = abiotic_tools.set_layers_function(canopy_layers=3, soil_layers=1)

    # test without dummy
    air_temperature = DataArray(
        [
            [22, 22, 22],
            [24, 24, 24],
            [26, 26, 26],
            [28, 28, 28],
            [30, 30, 30],
            [32, 32, 32],
        ],
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(1, (len(layers_function))),
            "layers_function": (
                "layers",
                layers_function[1 : (len(layers_function))],
            ),
            "cell_id": [0, 1, 2],
        },
    )

    result1D = abiotic_tools.calculate_latent_heat_vaporisation(data["temperature_2m"])
    result2D = abiotic_tools.calculate_latent_heat_vaporisation(air_temperature)

    xr.testing.assert_allclose(
        result1D,
        DataArray(
            [[43716.75, 44142.5, 43716.75]],
            dims=["layers", "cell_id"],
            coords={
                "layers": [6],
                "layers_function": ("layers", [layers_function[-1]]),
                "cell_id": [0, 1, 2],
            },
            name="latent_heat_vaporisation",
        ),
    )
    xr.testing.assert_allclose(
        result2D,
        DataArray(
            [
                [44057.35, 44057.35, 44057.35],
                [43972.2, 43972.2, 43972.2],
                [43887.05, 43887.05, 43887.05],
                [43801.9, 43801.9, 43801.9],
                [43716.75, 43716.75, 43716.75],
                [43631.6, 43631.6, 43631.6],
            ],
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(1, len(layers_function)),
                "layers_function": (
                    "layers",
                    layers_function[1 : len(layers_function)],
                ),
                "cell_id": [0, 1, 2],
            },
            name="latent_heat_vaporisation",
        ),
    )


def test_calculate_bulk_aero_resistance():
    """Test aerodynamic resistance calculation.

    TODO check why it does not work with dummy_data.
    """

    from virtual_rainforest.models.abiotic import abiotic_tools

    layers_function = abiotic_tools.set_layers_function(canopy_layers=3, soil_layers=1)

    wind_below_canopy = DataArray(
        [[0.1, 0.1, 0.1], [1, 0.5, 0.5], [2, 2, 5], [3, 4, 10], [5, 7, 12]],
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(1, (len(layers_function) - 1)),
            "layers_function": (
                "layers",
                layers_function[1 : (len(layers_function) - 1)],
            ),
            "cell_id": [0, 1, 2],
        },
    )

    result = abiotic_tools.calculate_aero_resistance(
        wind_speed=wind_below_canopy,
        heat_transfer_coefficient=50,
    )
    xr.testing.assert_allclose(
        result,
        DataArray(
            [
                [158.113883, 158.113883, 158.113883],
                [50.0, 70.710678, 70.710678],
                [35.355339, 35.355339, 22.36068],
                [28.867513, 25.0, 15.811388],
                [22.36068, 18.898224, 14.433757],
            ],
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(1, (len(layers_function) - 1)),
                "layers_function": (
                    "layers",
                    layers_function[1 : (len(layers_function) - 1)],
                ),
                "cell_id": [0, 1, 2],
            },
            name="aero_resistance",
        ),
    )


def test_set_layers_function():
    """Test layers string created correctly."""

    from virtual_rainforest.models.abiotic import abiotic_tools

    result = abiotic_tools.set_layers_function(canopy_layers=3, soil_layers=2)

    assert result == [
        "soil",
        "soil",
        "surface",
        "below",
        "canopy",
        "canopy",
        "canopy",
        "above",
    ]
