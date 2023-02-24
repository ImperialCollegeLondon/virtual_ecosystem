"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import numpy as np
import pytest
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.base_model import InitialisationError
from virtual_rainforest.models.soil.carbon import SoilCarbonPools


@pytest.fixture
def dummy_carbon_data():
    """Creates a dummy carbon data object for use in tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(cell_nx=4, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["maom"] = DataArray([2.5, 1.7, 4.5, 0.5], dims=["cell_id"])
    data["lmwc"] = DataArray([0.05, 0.02, 0.1, 0.005], dims=["cell_id"])
    data["pH"] = DataArray([3.0, 7.5, 9.0, 5.7], dims=["cell_id"])
    data["bulk_density"] = DataArray([1350.0, 1800.0, 1000.0, 1500.0], dims=["cell_id"])
    data["soil_moisture"] = DataArray([0.5, 0.7, 0.6, 0.2], dims=["cell_id"])
    data["soil_temperature"] = DataArray([35.0, 37.5, 40.0, 25.0], dims=["cell_id"])
    data["percent_clay"] = DataArray([80.0, 30.0, 10.0, 90.0], dims=["cell_id"])

    return data


def test_soil_carbon_class(dummy_carbon_data):
    """Test SoilCarbon class can be initialised."""

    # Check that initialisation succeeds as expected
    soil_carbon = SoilCarbonPools(dummy_carbon_data)

    assert (soil_carbon.maom == dummy_carbon_data["maom"]).all()
    assert (soil_carbon.lmwc == dummy_carbon_data["lmwc"]).all()


def test_bad_soil_carbon_class(caplog):
    """Test that negative soil pool values prevent class initialisation."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with a single cells.
    grid = Grid(cell_nx=1, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["maom"] = DataArray([2.5], dims=["cell_id"])
    data["lmwc"] = DataArray([-0.05], dims=["cell_id"])

    # Check that initialisation fails as expected
    with pytest.raises(InitialisationError):
        _ = SoilCarbonPools(data)

    expected_log_entries = (
        (
            INFO,
            "Adding data array for 'maom'",
        ),
        (
            INFO,
            "Adding data array for 'lmwc'",
        ),
        (
            ERROR,
            "Initial carbon pools contain at least one negative value!",
        ),
    )

    log_check(caplog, expected_log_entries)


def test_pool_updates(dummy_carbon_data):
    """Test that the two pool update functions work correctly."""

    # Initialise soil carbon class
    soil_carbon = SoilCarbonPools(dummy_carbon_data)

    dt = 0.5
    change_in_pools = [
        [1.988333e-4, 5.891712e-6, 7.17089e-5, 1.401810e-7],
        [-1.988333e-4, -5.891712e-6, -7.17089e-5, -1.401810e-7],
    ]
    end_maom = [2.50019883, 1.70000589, 4.50007171, 0.50000014]
    end_lmwc = [0.04980117, 0.01999411, 0.09992829, 0.00499986]

    delta_pools = soil_carbon.calculate_soil_carbon_updates(
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        dummy_carbon_data["soil_moisture"],
        dummy_carbon_data["soil_temperature"],
        dummy_carbon_data["percent_clay"],
        dt,
    )

    # Check that the updates are correctly calculated
    assert np.allclose(delta_pools.delta_maom, np.array(change_in_pools[0]))
    assert np.allclose(delta_pools.delta_lmwc, np.array(change_in_pools[1]))

    # Use this update to update the soil carbon pools
    soil_carbon.update_soil_carbon_pools(delta_pools)

    # Then check that pools are correctly incremented based on update
    assert np.allclose(soil_carbon.maom, np.array(end_maom))
    assert np.allclose(soil_carbon.lmwc, np.array(end_lmwc))


def test_mineral_association(dummy_carbon_data):
    """Test that mineral_association runs and generates the correct values."""

    output_l_to_m = [0.000397665, 1.178336e-5, 0.0001434178, 2.80359e-7]

    # Initialise soil carbon class
    soil_carbon = SoilCarbonPools(dummy_carbon_data)

    # Then calculate mineral association rate
    lmwc_to_maom = soil_carbon.mineral_association(
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        dummy_carbon_data["soil_moisture"],
        dummy_carbon_data["soil_temperature"],
        dummy_carbon_data["percent_clay"],
    )

    # Check that expected values are generated
    assert np.allclose(lmwc_to_maom, output_l_to_m)


def test_calculate_equilibrium_maom(dummy_carbon_data):
    """Test that equilibrium maom calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_equilibrium_maom

    Q_max = [2.385207e6, 1.980259e6, 647142.61, 2.805371e6]
    output_eqb_maoms = [19900.19, 969.4813, 832.6088, 742.4128]

    equib_maoms = calculate_equilibrium_maom(
        dummy_carbon_data["pH"], Q_max, dummy_carbon_data["lmwc"]
    )
    assert np.allclose(equib_maoms, np.array(output_eqb_maoms))


@pytest.mark.parametrize(
    "alternative,output_capacities,raises,expected_log_entries",
    [
        (
            None,
            [2.385207e6, 1.980259e6, 647142.61, 2.805371e6],
            does_not_raise(),
            (),
        ),
        (
            [156.0],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative clay content must be expressed as a percentage!"),),
        ),
        (
            [-9.0],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative clay content must be expressed as a percentage!"),),
        ),
    ],
)
def test_calculate_max_sorption_capacity(
    caplog,
    dummy_carbon_data,
    alternative,
    output_capacities,
    raises,
    expected_log_entries,
):
    """Test that max sorption capacity calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_max_sorption_capacity

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        if alternative:
            max_capacities = calculate_max_sorption_capacity(
                dummy_carbon_data["bulk_density"],
                np.array(alternative, dtype=np.float32),
            )
        else:
            max_capacities = calculate_max_sorption_capacity(
                dummy_carbon_data["bulk_density"], dummy_carbon_data["percent_clay"]
            )

        assert np.allclose(max_capacities, np.array(output_capacities))

    log_check(caplog, expected_log_entries)


def test_calculate_binding_coefficient(dummy_carbon_data):
    """Test that Langmuir binding coefficient calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_binding_coefficient

    output_coefs = [0.16826738, 0.02449064, 0.0128825, 0.05294197]

    binding_coefs = calculate_binding_coefficient(dummy_carbon_data["pH"])

    assert np.allclose(binding_coefs, np.array(output_coefs))


def test_convert_temperature_to_scalar(dummy_carbon_data):
    """Test that scalar_temperature runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_temperature_to_scalar

    output_scalars = [1.27113, 1.27196, 1.27263, 1.26344]

    temp_scalar = convert_temperature_to_scalar(dummy_carbon_data["soil_temperature"])

    assert np.allclose(temp_scalar, np.array(output_scalars))


@pytest.mark.parametrize(
    "alternative,output_scalars,raises,expected_log_entries",
    [
        (None, [0.750035, 0.947787, 0.880671, 0.167814], does_not_raise(), ()),
        (
            [-0.2],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative water content cannot go below zero or above one!"),),
        ),
        (
            [2.7],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative water content cannot go below zero or above one!"),),
        ),
    ],
)
def test_convert_moisture_to_scalar(
    caplog, dummy_carbon_data, alternative, output_scalars, raises, expected_log_entries
):
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_moisture_to_scalar

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        if alternative:
            moist_scalar = convert_moisture_to_scalar(
                np.array(alternative, dtype=np.float32)
            )
        else:
            moist_scalar = convert_moisture_to_scalar(
                dummy_carbon_data["soil_moisture"]
            )

        assert np.allclose(moist_scalar, np.array(output_scalars))

    log_check(caplog, expected_log_entries)
