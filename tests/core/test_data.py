"""Testing the Data class."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO
from pathlib import Path

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray, Dataset

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    argnames=["use_grid", "exp_err", "expected_log"],
    argvalues=[
        (
            False,
            pytest.raises(TypeError),
            ((CRITICAL, "Data must be initialised with a Grid object"),),
        ),
        (
            True,
            does_not_raise(),
            (),
        ),
    ],
)
def test_Data_init(caplog, use_grid, exp_err, expected_log):
    """Test the Data __init__: pretty basic."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

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
        pytest.param(  # Bad load - uses reserved dimension names
            DataArray(
                data=np.array(np.arange(9)),
                coords={"x": np.arange(9)},
                name="should_not_work",
            ),
            "should_not_work",
            pytest.raises(ValueError),
            (
                (INFO, "Adding data array for 'should_not_work'"),
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
        pytest.param(  # Replacing previous load from square_xy_coords
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="existing_var",
            ),
            "existing_var",
            does_not_raise(),
            ((INFO, "Replacing data array for 'existing_var'"),),
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
                name="add_without_axis",
            ),
            "add_without_axis",
            does_not_raise(),
            ((INFO, "Adding data array for 'add_without_axis'"),),
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
            "existing_var",
            does_not_raise(),
            None,
            [1, 2, 3, 4],
            id="should_get",
        ),
        pytest.param(
            "not_existing_var",
            pytest.raises(KeyError),
            "'not_existing_var'",
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
        pytest.param("existing_var", True),
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
    argnames=["name", "exp_log"],
    argvalues=[
        pytest.param(
            "temp",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
            ),
            id="simple_load",
        ),
        pytest.param(
            "elev",
            (
                (INFO, "Loading variable 'elev' from file:"),
                (INFO, "Replacing data array for 'elev'"),
            ),
            id="load_and_replace",
        ),
    ],
)
def test_Data_load_to_dataarray_naming(caplog, shared_datadir, name, exp_log):
    """Test the coding of the name handling and replacement."""

    # Setup a Data instance to match the example files generated in tests/core/data

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.core.readers import load_to_dataarray

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
    data["elev"] = DataArray(np.arange(100), dims=("cell_id",))
    caplog.clear()

    # Load the data from file
    datafile = shared_datadir / "cellid_coords.nc"

    data[name] = load_to_dataarray(file=datafile, var_name=name)

    # Check the naming has worked and the data are loaded
    assert name in data
    assert data[name].sum() == (20 * 100)

    # Check the error reports
    log_check(caplog, exp_log)


@pytest.fixture()
def fixture_load_data_grids(request):
    """Provides different grid types on request load data onto from file."""

    from virtual_rainforest.core.grid import Grid

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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
            ),
            20 * 100,
            id="vldr_spat__cellid_coords_any",
        ),
        pytest.param(
            ["__any__"],
            "cellid_coords_too_few.nc",
            pytest.raises(ValueError),
            "The data cell ids do not provide a one-to-one map onto grid " "cell ids.",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
            "The data cell ids do not provide a one-to-one map onto grid " "cell ids.",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
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

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.readers import load_to_dataarray

    # Skip combinations where validator does not supported this grid
    if not (
        ("__any__" in supported_grids)
        or (fixture_load_data_grids.grid_type in supported_grids)
    ):
        pytest.skip("Combination not tested")

    data = Data(fixture_load_data_grids)
    datafile = shared_datadir / filename

    with exp_error as err:
        data["temp"] = load_to_dataarray(file=datafile, var_name="temp")

        # Check the data is in fact loaded and that a simple sum of values matches
        assert "temp" in data
        assert data["temp"].sum() == exp_sum_val

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)

    return


@pytest.mark.parametrize(
    argnames=["file", "exp_error", "exp_msg", "exp_log"],
    argvalues=[
        pytest.param(
            "test.toml",
            does_not_raise(),
            None,
            (
                (INFO, "Loading data from configuration"),
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
                (INFO, "Loading variable 'prec' from file:"),
                (INFO, "Adding data array for 'prec'"),
                (INFO, "Loading variable 'elev' from file:"),
                (INFO, "Adding data array for 'elev'"),
                (INFO, "Loading variable 'vapd' from file:"),
                (INFO, "Adding data array for 'vapd'"),
            ),
            id="valid config",
        ),
        pytest.param(
            "test_dupes.toml",
            pytest.raises(ConfigurationError),
            "Data configuration did not load cleanly",
            (
                (INFO, "Loading data from configuration"),
                (CRITICAL, "Duplicate variable names in data configuration"),
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
                (INFO, "Loading variable 'prec' from file:"),
                (INFO, "Adding data array for 'prec'"),
                (INFO, "Loading variable 'elev' from file:"),
                (INFO, "Adding data array for 'elev'"),
                (INFO, "Loading variable 'elev' from file:"),
                (INFO, "Replacing data array for 'elev'"),
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
    caplog, shared_datadir, fixture_load_data_grids, file, exp_error, exp_msg, exp_log
):
    """Test the loading of data configuration strings.

    TODO - Could mock load_to_dataarray to avoid needing real files and just test the
           config loader part of the mechanism
    TODO - The test TOML files here are _very_ minimal and are going to be fragile to
           required fields being updated. They explicitly load no modules to moderate
           this risk.
    """

    # Setup a Data instance to match the example files generated in tests/core/data

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.data import Data

    # Skip combinations where loader does not supported this grid
    data = Data(fixture_load_data_grids)
    file = [shared_datadir / file]

    cfg = Config(file)
    caplog.clear()

    # Edit the paths loaded to point to copies in shared_datadir
    for each_var in cfg["core"]["data"]["variable"]:
        each_var["file"] = shared_datadir / each_var["file"]

    with exp_error as err:
        data.load_data_config(data_config=cfg["core"]["data"])

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames="vname, axname, result, err_ctxt, err_message",
    argvalues=[
        ("temp", "spatial", True, does_not_raise(), None),
        ("temp", "testing", False, does_not_raise(), None),
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
            "temp",
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
    fixture_data["temp"] = da

    # Add a data array _incorrectly_
    fixture_data.data["incorrect"] = da

    with err_ctxt as err:
        assert result == fixture_data.on_core_axis(vname, axname)

    if err_message:
        assert str(err.value) == err_message


@pytest.mark.parametrize(
    argnames=["out_path", "raises", "save_specific", "exp_log"],
    argvalues=[
        ("./initial.nc", does_not_raise(), False, ()),
        ("./initial.nc", does_not_raise(), True, ()),
        (
            "bad_folder/initial.nc",
            pytest.raises(ConfigurationError),
            "",
            (
                (
                    CRITICAL,
                    "The user specified output directory (bad_folder) doesn't exist!",
                ),
            ),
        ),
        (
            "pyproject.toml/initial.nc",
            pytest.raises(ConfigurationError),
            False,
            (
                (
                    CRITICAL,
                    "The user specified output folder (pyproject.toml) isn't a "
                    "directory!",
                ),
            ),
        ),
        (
            "./final.nc",
            pytest.raises(ConfigurationError),
            False,
            (
                (
                    CRITICAL,
                    "A file in the user specified output folder (.) already makes use "
                    "of the specified output file name (final.nc), this file should "
                    "either be renamed or deleted!",
                ),
            ),
        ),
    ],
)
def test_save_to_netcdf(
    mocker, caplog, dummy_carbon_data, out_path, save_specific, raises, exp_log
):
    """Test that data object can save as NetCDF."""

    # Configure the mock to return a specific list of files
    if out_path == "./final.nc":
        mock_content = mocker.patch("virtual_rainforest.core.config.Path.exists")
        mock_content.return_value = True

    with raises:
        if save_specific:
            dummy_carbon_data.save_to_netcdf(
                Path(out_path), variables_to_save=["soil_c_pool_lmwc"]
            )
        else:
            dummy_carbon_data.save_to_netcdf(Path(out_path))

        # Load in netcdf data to check the contents
        saved_data = xr.open_dataset(Path(out_path))

        # Then check that expected keys are in it
        if save_specific:
            assert "soil_c_pool_lmwc" in saved_data
            assert "soil_c_pool_maom" not in saved_data
        else:
            assert "soil_c_pool_lmwc" in saved_data
            assert "soil_c_pool_maom" in saved_data

        # Close the dataset (otherwise windows has a problem)
        saved_data.close()

        # Remove generated output file
        Path(out_path).unlink()

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames=["append_path", "raises", "error_msg"],
    argvalues=[
        (
            "initial.nc",
            pytest.raises(ConfigurationError),
            "The continuous data file (initial.nc) doesn't exist to be appended to!",
        ),
        (
            "output.nc",
            does_not_raise(),
            "",
        ),
    ],
)
def test_append_to_netcdf(dummy_carbon_data, append_path, raises, error_msg):
    """Test that data object can append to an existing NetCDF file."""

    # Create initial netcdf file
    dummy_carbon_data.save_to_netcdf(
        Path("output.nc"), variables_to_save=["soil_c_pool_lmwc", "soil_temperature"]
    )

    with raises as excep:
        # Change data to check that appending works
        dummy_carbon_data["soil_c_pool_lmwc"] = DataArray(
            [0.1, 0.05, 0.2, 0.01], dims=["cell_id"], coords={"cell_id": [0, 1, 2, 3]}
        )
        # Append data to netcdf file
        dummy_carbon_data.append_to_netcdf(
            Path(append_path),
            variables_to_save=["soil_c_pool_lmwc", "soil_temperature"],
        )

        # TODO - This second call to append doesn't seem to do anything, work out why
        # Append data again to netcdf file to check that multiple appends work
        dummy_carbon_data["soil_temperature"][13][0] = 15.0
        dummy_carbon_data.append_to_netcdf(
            Path(append_path),
            variables_to_save=["soil_c_pool_lmwc", "soil_temperature"],
        )

        # Load file, and then check that contents meet expectation
        saved_data = xr.open_dataset(Path(append_path))
        xr.testing.assert_allclose(
            saved_data["soil_c_pool_lmwc"],
            DataArray(
                [[0.05, 0.02, 0.1, 0.005], [0.1, 0.05, 0.2, 0.01]],
                dims=["time_index", "cell_id"],
                coords={"cell_id": [0, 1, 2, 3], "time_index": [0, 1]},
            ),
        )
        # TODO - Check soil temp values as well.

    # Remove generated output file
    Path("output.nc").unlink()

    # Finally check that the error message was as expected
    if error_msg:
        assert str(excep.value) == error_msg


def test_Data_add_from_dict(dummy_climate_data):
    """Test reading from dictionary."""

    from virtual_rainforest.core.data import Data

    var_dict = {
        "air_temperature": DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            coords=dummy_climate_data["air_temperature_ref"].coords,
            name="air_temperature_ref",
        ),
        "mean_annual_temperature": DataArray(
            np.full((3), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
        "new_variable": DataArray(
            np.full((3), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="new_variable",
        ),
    }

    Data.add_from_dict(dummy_climate_data, var_dict)

    xr.testing.assert_allclose(
        dummy_climate_data["air_temperature"],
        DataArray(
            np.full((3, 3), 20),
            dims=["cell_id", "time"],
            coords=dummy_climate_data["air_temperature"].coords,
            name="air_temperature",
        ),
    )
    xr.testing.assert_allclose(
        dummy_climate_data["mean_annual_temperature"],
        DataArray(
            np.full((3), 40),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="mean_annual_temperature",
        ),
    )
    xr.testing.assert_allclose(
        dummy_climate_data["new_variable"],
        DataArray(
            np.full((3), 100),
            dims=["cell_id"],
            coords=dummy_climate_data["mean_annual_temperature"].coords,
            name="new_variable",
        ),
    )
