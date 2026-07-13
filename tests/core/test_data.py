"""Testing the Data class."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO, WARNING

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray, Dataset
from xarray.testing import assert_allclose

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    argnames=["use_grid", "exp_err", "expected_log"],
    argvalues=[
        pytest.param(
            False,
            pytest.raises(TypeError),
            ((CRITICAL, "Data must be initialised with a Grid object"),),
            id="init_not_grid",
        ),
        pytest.param(True, does_not_raise(), (), id="init_is_grid"),
    ],
)
def test_Data_init(caplog, use_grid, exp_err, expected_log):
    """Test the Data __init__: pretty basic."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    caplog.clear()

    # Switch on what to provide as grid
    grid = Grid() if use_grid else 1

    with exp_err:
        _ = Data(grid)

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=[
        "darray",
        "name",
        "exp_err",
        "exp_log",
        "exp_vals",
    ],
    argvalues=[
        pytest.param(  # Bad load - not a dataarray
            np.array([1, 2, 3]),
            "air_temperature",
            pytest.raises(TypeError),
            ((CRITICAL, "Only DataArray objects can be added to Data instances"),),
            None,
            id="not_dataarray",
        ),
        pytest.param(  # Bad load - dataset
            Dataset({"temp": np.array([1, 2, 3])}),
            "air_temperature",
            pytest.raises(TypeError),
            ((CRITICAL, "Only DataArray objects can be added to Data instances"),),
            None,
            id="dataset_not_datarray",
        ),
        pytest.param(  # Bad load - uses x without y and does not match validator
            DataArray(
                data=np.array(np.arange(9)),
                coords={"x": np.arange(9)},
                name="should_not_work",
            ),
            "air_temperature",
            pytest.raises(ValueError),
            (
                (INFO, "Adding data array for 'air_temperature'"),
                (
                    CRITICAL,
                    "DataArray uses 'spatial' axis dimension names but does "
                    "not match a validator",
                ),
            ),
            None,
            id="uses_reserved_dims",
        ),
        pytest.param(  # Valid load from square_xy_coords
            DataArray(
                data=np.array([[0, 1], [2, 3]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="air_temperature",
            ),
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            [0, 1, 2, 3],
            id="valid_square_xy_coords",
        ),
        pytest.param(  # Replacing pre-populated variable in fixture
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="atmospheric_co2",
            ),
            "atmospheric_co2",
            does_not_raise(),
            ((INFO, "Replacing data array for 'atmospheric_co2'"),),
            [4, 5, 6, 7],
            id="replacing_data",
        ),
        pytest.param(  # Good load from square_xy_dims
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                dims=("y", "x"),
                name="air_temperature",
            ),
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_square_xy_dims",
        ),
        pytest.param(  # Good load from any_cellid_coords
            DataArray(
                data=np.array([4, 5, 6, 7]),
                coords={"cell_id": [0, 1, 2, 3]},
                name="air_temperature",
            ),
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_any_cellid_coords",
        ),
        pytest.param(  # Good load from any_cellid_dim
            DataArray(
                data=np.array([4, 5, 6, 7]),
                dims=("cell_id",),
                name="air_temperature",
            ),
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_any_cell_id_dims",
        ),
        pytest.param(  # Good load - does not match axes
            DataArray(
                data=np.array(np.arange(9)),
                coords={"nope": np.arange(9)},
                name="air_temperature",
            ),
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            np.arange(9),
            id="add_without_axis",
        ),
    ],
)
def test_Data_setitem(caplog, fixture_data, darray, name, exp_err, exp_log, exp_vals):
    """Test the __setitem__ method.

    Note that fixture_data is edited to create existing variables
    """

    with exp_err:
        fixture_data[name] = darray
        assert name in fixture_data
        assert np.allclose(fixture_data[name].values, exp_vals)

    # Check the error reports
    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames=["var_name", "exp_err", "exp_msg", "exp_vals"],
    argvalues=[
        pytest.param(
            "atmospheric_co2",
            does_not_raise(),
            None,
            [1, 2, 3, 4],
            id="should_get",
        ),
        pytest.param(
            "not_existing_var",
            pytest.raises(KeyError),
            """"No variable named 'not_existing_var'. """
            '''Variables on the dataset include ['atmospheric_co2']"''',
            None,
            id="should_not_get",
        ),
    ],
)
def test_Data_getitem(fixture_data, var_name, exp_err, exp_msg, exp_vals):
    """Test the __getitem__ method.

    Note that fixture_data is edited to include an existing variable
    """

    with exp_err as err:
        darray = fixture_data[var_name]
        assert np.allclose(darray.values, exp_vals)

    # Check the error reports
    if err:
        assert str(err.value) == exp_msg


@pytest.mark.parametrize(
    argnames=["var_name", "expected"],
    argvalues=[
        pytest.param("atmospheric_co2", True),
        pytest.param("not_existing_var", False),
    ],
)
def test_Data_contains(fixture_data, var_name, expected):
    """Test the __contains__ method.

    Note that fixture_data is edited to include an existing variable
    """

    # Check the return boolean
    assert (var_name in fixture_data) == expected


@pytest.mark.parametrize(
    argnames=["var_names", "exp_log"],
    argvalues=[
        pytest.param(
            ["air_temperature"],
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
            ),
            id="simple_load",
        ),
        pytest.param(
            ["elevation"],
            (
                (INFO, "Loading variables from file"),
                (INFO, "Replacing data array for 'elevation'"),
            ),
            id="load_and_replace",
        ),
    ],
)
def test_Data_load_to_dataarray_naming(caplog, shared_datadir, var_names, exp_log):
    """Test the coding of the name handling and replacement."""

    # Setup a Data instance to match the example files generated in tests/core/data

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.core.readers import load_to_dataarray

    caplog.clear()

    grid = Grid(
        grid_type="square",
        cell_nx=10,
        cell_ny=10,
        cell_area=10000,
        xoff=500000,
        yoff=200000,
    )
    data = Data(grid)

    # Create an existing variable to test replacement
    data["elevation"] = DataArray(np.arange(100), dims=("cell_id",))
    caplog.clear()

    # Load the data from file
    datafile = shared_datadir / "cellid_coords.nc"

    results = load_to_dataarray(file=datafile, var_names=var_names)
    for ky, val in results.items():
        data[ky] = val

    for name in var_names:
        # Check the naming has worked and the data are loaded
        assert name in data
        assert data[name].sum() == (20 * 100)

    # Check the error reports
    log_check(caplog, exp_log)


@pytest.fixture()
def fixture_load_data_grids(request):
    """Provides different grid types on request load data onto from file."""

    from virtual_ecosystem.core.grid import Grid

    grid = Grid(
        grid_type=request.param,
        cell_nx=10,
        cell_ny=10,
        cell_area=10000,
        xoff=500000,
        yoff=200000,
    )

    return grid


@pytest.mark.parametrize(
    argnames=[
        "supported_grids",
        "filename",
        "exp_error",
        "exp_msg",
        "exp_log",
        "exp_sum_val",
    ],
    argvalues=[
        pytest.param(
            ["__any__"],
            "this_data_format.not_handled",
            pytest.raises(ValueError),
            "No file format loader provided for .not_handled",
            ((CRITICAL, "No file format loader provided for .not_handled"),),
            None,
            id="unhandled file format",
        ),
        pytest.param(
            ["__any__"],
            "cellid_dims.nc",
            does_not_raise(),
            None,
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
            ),
            20 * 100,
            id="vldr_spat__cellid_dim_any",
        ),
        pytest.param(
            ["__any__"],
            "cellid_dim_too_few.nc",
            pytest.raises(ValueError),
            "Grid defines 100 cells, data provides 60",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (CRITICAL, "Grid defines 100 cells, data provides 60"),
            ),
            None,
            id="vldr_spat__cellid_dim_any_too_few",
        ),
        pytest.param(
            ["__any__"],
            "cellid_dim_too_many.nc",
            pytest.raises(ValueError),
            "Grid defines 100 cells, data provides 200",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (CRITICAL, "Grid defines 100 cells, data provides 200"),
            ),
            None,
            id="vldr_spat__cellid_dim_any_too_many",
        ),
        pytest.param(
            ["__any__"],
            "cellid_coords.nc",
            does_not_raise(),
            None,
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
            ),
            20 * 100,
            id="vldr_spat__cellid_coords_any",
        ),
        pytest.param(
            ["__any__"],
            "cellid_coords_too_few.nc",
            pytest.raises(ValueError),
            "The data cell ids do not provide a one-to-one map onto grid cell ids.",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (
                    CRITICAL,
                    "The data cell ids do not provide a one-to-one map onto grid "
                    "cell ids.",
                ),
            ),
            None,
            id="vldr_spat__cellid_coords_any_too_few",
        ),
        pytest.param(
            ["__any__"],
            "cellid_coords_bad_cellid.nc",
            pytest.raises(ValueError),
            "The data cell ids do not provide a one-to-one map onto grid cell ids.",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (
                    CRITICAL,
                    "The data cell ids do not provide a one-to-one map onto grid "
                    "cell ids.",
                ),
            ),
            None,
            id="vldr_spat__cellid_coords_any_bad_cellid",
        ),
        pytest.param(
            ["square"],
            "xy_dim.nc",
            does_not_raise(),
            None,
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
            ),
            20 * 100,
            id="vldr_spat__xy_dim_square",
        ),
        pytest.param(
            ["square"],
            "xy_dim_small.nc",
            pytest.raises(ValueError),
            "Data XY dimensions do not match square grid",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (CRITICAL, "Data XY dimensions do not match square grid"),
            ),
            None,
            id="vldr_spat__xy_dim_square_small",
        ),
        pytest.param(
            ["square"],
            "xy_coords.nc",
            does_not_raise(),
            None,
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
            ),
            20 * 100,
            id="vldr_spat__xy_coords_square",
        ),
        pytest.param(
            ["square"],
            "xy_coords_small.nc",
            pytest.raises(ValueError),
            "Mapped points do not cover all cells.",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (CRITICAL, "Mapped points do not cover all cells."),
            ),
            None,
            id="vldr_spat__xy_coords_square_small",
        ),
        pytest.param(
            ["square"],
            "xy_coords_shifted.nc",
            pytest.raises(ValueError),
            "Mapped points fall outside grid.",
            (
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (CRITICAL, "Mapped points fall outside grid."),
            ),
            None,
            id="vldr_spat__xy_coords_square_shifted",
        ),
    ],
)
@pytest.mark.parametrize(
    # On request, use the fixture to provide different grids
    "fixture_load_data_grids",
    ["square", "hexagon"],
    indirect=True,
)
def test_Data_load_to_dataarray_data_handling(
    caplog,
    fixture_load_data_grids,
    supported_grids,
    shared_datadir,
    filename,
    exp_error,
    exp_msg,
    exp_log,
    exp_sum_val,
):
    """Test the loading of data from file formats against various grids.

    This tests the data handling, and test_Data_load_to_dataarray_naming handles the
    data name and name replacement functionality
    """

    # Setup a Data instance to match the example files generated in tests/core/data

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.readers import load_to_dataarray

    caplog.clear()

    # Skip combinations where validator does not supported this grid
    if not (
        ("__any__" in supported_grids)
        or (fixture_load_data_grids.grid_type in supported_grids)
    ):
        pytest.skip("Combination not tested")

    data = Data(fixture_load_data_grids)
    datafile = shared_datadir / filename

    with exp_error as err:
        results = load_to_dataarray(file=datafile, var_names=["air_temperature"])
        data["air_temperature"] = results["air_temperature"]

        # Check the data is in fact loaded and that a simple sum of values matches
        assert "air_temperature" in data
        assert data["air_temperature"].sum() == exp_sum_val

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames=["cfg_data", "exp_error", "exp_msg", "exp_log"],
    argvalues=[
        pytest.param(
            {
                "core": {
                    "data": {
                        "variable": [
                            {
                                "file_path": "cellid_coords.nc",
                                "var_name": "air_temperature",
                            },
                            {
                                "file_path": "cellid_coords.nc",
                                "var_name": "precipitation",
                            },
                            {"file_path": "cellid_coords.nc", "var_name": "elevation"},
                            {
                                "file_path": "cellid_coords.nc",
                                "var_name": "vapour_pressure_deficit",
                            },
                        ]
                    }
                }
            },
            does_not_raise(),
            None,
            (
                (INFO, "Loading data from configuration"),
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (INFO, "Adding data array for 'precipitation'"),
                (INFO, "Adding data array for 'elevation'"),
                (INFO, "Adding data array for 'vapour_pressure_deficit'"),
            ),
            id="valid config",
        ),
        pytest.param(
            {"core": {"data": {"variable": []}}},
            does_not_raise(),
            None,
            (
                (INFO, "Loading data from configuration"),
                (WARNING, "No data sources defined in the data configuration."),
            ),
            id="no data",
        ),
        pytest.param(
            {
                "core": {
                    "data": {
                        "variable": [
                            {
                                "file_path": "cellid_coords.nc",
                                "var_name": "air_temperature",
                            },
                            {
                                "file_path": "cellid_coords.nc",
                                "var_name": "precipitation",
                            },
                            {"file_path": "cellid_coords.nc", "var_name": "elevation"},
                            {"file_path": "cellid_coords.nc", "var_name": "elevation"},
                        ]
                    }
                }
            },
            pytest.raises(ConfigurationError),
            "Data configuration did not load cleanly - check log",
            (
                (INFO, "Loading data from configuration"),
                (ERROR, "Duplicate variable names in data configuration"),
                (INFO, "Loading variables from file"),
                (INFO, "Adding data array for 'air_temperature'"),
                (INFO, "Adding data array for 'precipitation'"),
                (INFO, "Adding data array for 'elevation'"),
                (CRITICAL, "Data configuration did not load cleanly - check log"),
            ),
            id="repeated names",
        ),
    ],
)
@pytest.mark.parametrize(
    # On request, use the fixture to provide different grids
    "fixture_load_data_grids",
    ["square", "hexagon"],
    indirect=True,
)
def test_Data_load_from_config(
    caplog,
    shared_datadir,
    fixture_load_data_grids,
    cfg_data,
    exp_error,
    exp_msg,
    exp_log,
):
    """Test the loading of data configuration strings.

    TODO - The test TOML files here are _very_ minimal and are going to be fragile to
           required fields being updated. They explicitly load no modules to moderate
           this risk.
    """

    # Setup a Data instance to match the example files generated in tests/core/data

    from virtual_ecosystem.core.config_builder import (
        generate_configuration,
    )
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.model_config import CoreConfiguration

    # Update the paths to point to copies of actual files in shared_datadir
    # This has to happen before generating the configuration, because the config
    # BaseModel requires that files actually exist.
    for each_var in cfg_data["core"]["data"]["variable"]:
        each_var["file_path"] = shared_datadir / each_var["file_path"]

    data = Data(fixture_load_data_grids)
    config = generate_configuration(cfg_data)

    core_config = config.get_subconfiguration("core", CoreConfiguration)

    caplog.clear()

    with exp_error as err:
        data.load_data_config(config=core_config)

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames="vname, axname, result, err_ctxt, err_message",
    argvalues=[
        ("air_temperature", "spatial", True, does_not_raise(), None),
        ("air_temperature", "testing", False, does_not_raise(), None),
        (
            "missing",
            "spatial",
            False,
            pytest.raises(ValueError),
            "Unknown variable name: missing",
        ),
        (
            "incorrect",
            "spatial",
            False,
            pytest.raises(ValueError),
            "Missing variable validation data: incorrect",
        ),
        (
            "air_temperature",
            "missing",
            False,
            pytest.raises(ValueError),
            "Unknown core axis name: missing",
        ),
    ],
)
def test_on_core_axis(
    new_axis_validators, fixture_data, vname, axname, result, err_ctxt, err_message
):
    """Test the on_core_axis method."""

    # Add a data array properly
    da = DataArray([1, 2, 3, 4], dims=("cell_id",), name="temp")
    fixture_data["air_temperature"] = da

    # Add a data array _incorrectly_
    fixture_data.data["incorrect"] = da

    with err_ctxt as err:
        assert result == fixture_data.on_core_axis(vname, axname)

    if err_message:
        assert str(err.value) == err_message


@pytest.mark.parametrize(argnames="group", argvalues=("vars", None))
@pytest.mark.parametrize(argnames="save_specific", argvalues=(False, True))
def test_save_to_zarr(
    shared_datadir,
    dummy_litter_data,
    group,
    save_specific,
):
    """Test that data object can save as Zarr.

    This tests combinations of:
    1. writing all or some variables, and
    2. writing data to a group within the Zarr store.
    """

    out_path = shared_datadir / "test_output.zarr"

    if save_specific:
        dummy_litter_data.save_to_zarr(
            output_file_path=out_path,
            group=group,
            variables_to_save=["litter_pool_woody_cnp"],
        )
    else:
        dummy_litter_data.save_to_zarr(output_file_path=out_path, group=group)

    # Load in zarr data to check the contents
    # NOTE - For some reason, unless the engine is specified, the xarray process to
    #        guess the engine runs into a permissions issue.
    saved_data = xr.open_dataset(out_path, group=group, engine="zarr")

    # Then check that expected keys are in it and the values match
    assert "litter_pool_woody_cnp" in saved_data
    assert_allclose(
        dummy_litter_data["litter_pool_woody_cnp"],
        saved_data["litter_pool_woody_cnp"],
    )

    if save_specific:
        assert "litter_pool_above_metabolic_cnp" not in saved_data
    else:
        assert "litter_pool_above_metabolic_cnp" in saved_data

    # Close the dataset (otherwise windows has a problem)
    saved_data.close()


@pytest.mark.parametrize(argnames="group", argvalues=("vars", None))
@pytest.mark.parametrize(argnames="save_specific", argvalues=(False, True))
def test_save_current_state_to_zarr(
    shared_datadir, dummy_litter_data, group, save_specific
):
    """Test that the save current state method appends correctly."""

    out_path = shared_datadir / "test_output.zarr"

    # Write data to zarr
    var_to_save = ["lignin_woody", "soil_temperature"] if save_specific else []
    dummy_litter_data.save_current_state_to_zarr(
        out_path,
        group=group,
        variables_to_save=var_to_save,
        time_index=0,
        timestamp=np.datetime64("2000-01-01"),
    )

    # NOTE - For some reason, unless the engine is specified, the xarray process to
    #        guess the engine runs into a permissions issue.
    saved_data = xr.open_dataset(out_path, group=group, engine="zarr")

    assert "lignin_woody" in saved_data
    # The saved data should now have coords with time_index in them but otherwise be the
    # same as the values in the data object
    vals = dummy_litter_data["lignin_woody"].to_numpy().copy()
    expected = xr.DataArray(
        vals[None, :],
        coords=dict(time_index=np.array([0]), cell_id=np.arange(4)),
    )
    assert_allclose(expected, saved_data["lignin_woody"])

    if save_specific:
        assert "litter_pool_above_metabolic_cnp" not in saved_data
    else:
        assert "litter_pool_above_metabolic_cnp" in saved_data

    # Alter the data and export again to the next step
    dummy_litter_data["lignin_woody"] *= 2

    dummy_litter_data.save_current_state_to_zarr(
        out_path,
        group=group,
        variables_to_save=var_to_save,
        time_index=1,
        timestamp=np.datetime64("2001-01-01"),
    )

    # Load fil again, and then check that contents still meet expectation
    saved_data = xr.open_dataset(out_path, group=group)

    assert "lignin_woody" in saved_data
    # The saved data should now have coords with time_index in them but otherwise be the
    # same as the values in the data object
    expected = xr.DataArray(
        np.vstack([vals, vals * 2]),
        coords=dict(time_index=np.array([0, 1]), cell_id=np.arange(4)),
    )
    assert_allclose(expected, saved_data["lignin_woody"])

    if save_specific:
        assert "litter_pool_above_metabolic_cnp" not in saved_data
    else:
        assert "litter_pool_above_metabolic_cnp" in saved_data

    # Finally, close the dataset
    saved_data.close()


def test_Data_add_from_dict(fixture_core_components, dummy_climate_data):
    """Test adding and replacing data from a dictionary."""

    from virtual_ecosystem.core.data import Data

    var_dict = {
        "mean_annual_temperature": DataArray(
            np.full((fixture_core_components.grid.n_cells), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
        "elevation": DataArray(
            np.full((fixture_core_components.grid.n_cells), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="elevation",
        ),
    }

    Data.add_from_dict(dummy_climate_data, var_dict)

    xr.testing.assert_allclose(
        dummy_climate_data["mean_annual_temperature"],
        DataArray(
            np.full((fixture_core_components.grid.n_cells), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
    )
    xr.testing.assert_allclose(
        dummy_climate_data["elevation"],
        DataArray(
            np.full((fixture_core_components.grid.n_cells), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="elevation",
        ),
    )
