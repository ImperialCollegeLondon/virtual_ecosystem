"""Test data loading and validation."""
from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, INFO

import numpy as np
import pytest
from xarray import DataArray

from .conftest import log_check


@pytest.mark.parametrize(
    argnames=["file_types", "expected_log"],
    argvalues=[
        (  # Single file type - add and replace
            (".xyz",),
            ((DEBUG, "Adding data loader function for .xyz"),),
        ),
        (
            (".xyz",),
            ((DEBUG, "Replacing existing data loader function for .xyz"),),
        ),
        (  # Tuple of file types, add and replace
            (".abc", ".def"),
            (
                (DEBUG, "Adding data loader function for .abc"),
                (DEBUG, "Adding data loader function for .def"),
            ),
        ),
        (  # Tuple of file types, add and replace
            (".abc", ".ghi"),
            (
                (DEBUG, "Replacing existing data loader function for .abc"),
                (DEBUG, "Adding data loader function for .ghi"),
            ),
        ),
    ],
)
def test_file_format_loader(caplog, file_types, expected_log):
    """Tests the file format loader decorator.

    TODO - Note that the test here is actually changing the live DATA_LOADER_REGISTRY,
           so that the order of execution of the parameterisation for the tests are not
           independent of one another.
    """

    # Import register_data_loader - this triggers the registration of existing data
    # loaders so need to clear those log messages before trying new ones
    from virtual_rainforest.core.data import register_file_format_loader
    from virtual_rainforest.core.logger import LOGGER

    # Capture debug/setup messages
    LOGGER.setLevel("DEBUG")

    caplog.clear()

    # Decorate a mock function to test the failure modes
    @register_file_format_loader(file_types=file_types)
    def mock_function():
        return

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["signature", "exp_err", "expected_log"],
    argvalues=[
        (  # Unknown singleton
            (("zzz",), ("zzz",), ("penrose",)),
            pytest.raises(AttributeError),
            ((CRITICAL, "Unknown grid type 'penrose' decorating mock_function"),),
        ),
        (  # Unknown grid in 2 tuple
            (("zzz",), ("zzz",), ("square", "penrose")),
            pytest.raises(AttributeError),
            ((CRITICAL, "Unknown grid type 'penrose' decorating mock_function"),),
        ),
        (  # Succesful singleton
            (("zzz",), ("zzz",), ("square",)),
            does_not_raise(),
            ((DEBUG, "Adding spatial loader: mock_function"),),
        ),
        (  # Succesful 2 tuple
            (("zzz",), ("zzz",), ("square", "hexagon")),
            does_not_raise(),
            ((DEBUG, "Adding spatial loader: mock_function"),),
        ),
    ],
)
def test_add_spatial_loader(caplog, signature, exp_err, expected_log):
    """Tests the file format loader decorator.

    TODO - Note that the test here is actually changing the live DataArrayLoader,
           so that the order of execution of the parameterisation for the tests are not
           independent of one another.
    """

    # Import register_data_loader - this triggers the registration of existing data
    # loaders so need to clear those log messages before trying new ones
    from virtual_rainforest.core.data import add_spatial_loader
    from virtual_rainforest.core.logger import LOGGER

    # Capture debug/setup messages
    LOGGER.setLevel("DEBUG")

    caplog.clear()

    # Decorate a mock function to test the failure modes
    with exp_err:

        @add_spatial_loader(signature)
        def mock_function():
            return

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["file", "file_var", "exp_err", "expected_log"],
    argvalues=[
        (
            "not_there.nc",
            "irrelevant",
            pytest.raises(FileNotFoundError),
            ((CRITICAL, "Data file not found"),),
        ),
        (
            "garbage.nc",
            "irrelevant",
            pytest.raises(ValueError),
            ((CRITICAL, "Could not load data from"),),
        ),
        (
            "xy_dim.nc",
            "missing",
            pytest.raises(KeyError),
            ((CRITICAL, "Variable missing not found in"),),
        ),
        (
            "xy_dim.nc",
            "temp",
            does_not_raise(),
            (),
        ),
    ],
)
def test_load_netcdf(datadir, caplog, file, file_var, exp_err, expected_log):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import load_netcdf

    with exp_err:
        darray = load_netcdf(datadir / file, file_var)
        assert isinstance(darray, DataArray)

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (
            {"grid_type": "square"},
            DataArray(data=np.arange(50), dims=("cell_id")),
            pytest.raises(ValueError),
            "Grid defines 100 cells, data provides 50",
            None,
        ),
        (
            {"grid_type": "square"},
            DataArray(data=np.arange(100), dims=("cell_id")),
            does_not_raise(),
            None,
            np.arange(100),
        ),
    ],
)
def test_spld_cellid_dim_any(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, spld_cellid_dim_any
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = spld_cellid_dim_any(data, darray)
        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (  # grid cell ids not covered by data
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(data=np.arange(6), coords={"cell_id": [1, 2, 3, 4, 5, 9]}),
            pytest.raises(ValueError),
            "The data cell ids are not a superset of grid cell ids.",
            None,
        ),
        (  # Duplicate ids in data
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(data=np.arange(6), coords={"cell_id": [0, 1, 2, 5, 4, 5]}),
            pytest.raises(ValueError),
            "The data cell ids contain duplicate values.",
            None,
        ),
        (  # - same size and order
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(data=np.arange(6), coords={"cell_id": [0, 1, 2, 3, 4, 5]}),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
        (  # - same order but more ids in cell data
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(
                data=np.arange(9), coords={"cell_id": [0, 1, 2, 3, 4, 5, 6, 7, 8]}
            ),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
        (  # - different order
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(
                data=np.array([5, 3, 1, 0, 4, 2]),
                coords={"cell_id": [5, 3, 1, 0, 4, 2]},
            ),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
        (  # - different order and subsetting
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(
                data=np.array([6, 5, 7, 3, 1, 0, 4, 2, 8]),
                coords={"cell_id": [6, 5, 7, 3, 1, 0, 4, 2, 8]},
            ),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
    ],
)
def test_spld_cellid_coord_any(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, spld_cellid_coord_any
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = spld_cellid_coord_any(data, darray)

        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (  # Wrong size
            {"grid_type": "square", "cell_nx": 2, "cell_ny": 3},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]), dims=("y", "x")
            ),
            pytest.raises(ValueError),
            "Data XY dimensions do not match square grid",
            None,
        ),
        (  # All good
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]), dims=("y", "x")
            ),
            does_not_raise(),
            None,
            np.arange(9),
        ),
    ],
)
def test_spld_xy_dim_square(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, spld_xy_dim_square
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = spld_xy_dim_square(data, darray)
        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (  # Coords on cell boundaries
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
                coords={"y": [2, 1, 0], "x": [2, 1, 0]},
            ),
            pytest.raises(ValueError),
            "Mapped points fall on cell boundaries.",
            None,
        ),
        (  # Does not cover cells
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5]]),
                coords={"y": [2.5, 1.5], "x": [2.5, 1.5, 0.5]},
            ),
            pytest.raises(ValueError),
            "Mapped points do not cover all cells.",
            None,
        ),
        (  # Irregular sampling on y axis gives multiple points in bottom row
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]]),
                coords={"y": [2.5, 1.5, 0.5, 0.4], "x": [0.5, 1.5, 2.5]},
            ),
            pytest.raises(ValueError),
            "Some cells contain more than one point.",
            None,
        ),
        (  # All good
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
                coords={"y": [2.5, 1.5, 0.5], "x": [0.5, 1.5, 2.5]},
            ),
            does_not_raise(),
            None,
            np.arange(9),
        ),
    ],
)
def test_spld_xy_coord_square(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, spld_xy_coord_square
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = spld_xy_coord_square(data, darray)
        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


# Testing the Data class


@pytest.mark.parametrize(
    argnames=["use_grid", "exp_err", "expected_log"],
    argvalues=[
        (
            False,
            pytest.raises(ValueError),
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
        "replace",
        "exp_name",
        "exp_err",
        "exp_log",
        "exp_vals",
    ],
    argvalues=[
        pytest.param(  # Bad load - missing name
            DataArray(
                data=np.array([[0, 1], [2, 3]]),
                coords={"y": [2, 1], "x": [1, 2]},
            ),
            False,
            "air_temperature",
            pytest.raises(ValueError),
            ((CRITICAL, "Cannot add data array with unnamed variable"),),
            None,
            id="missing_name",
        ),
        pytest.param(  # Bad load - no known loader
            DataArray(
                data=np.array(np.arange(9)),
                coords={"nope": np.arange(9)},
                name="should_not_work",
            ),
            False,
            "air_temperature",
            pytest.raises(ValueError),
            (
                (INFO, "Adding data array for 'should_not_work'"),
                (CRITICAL, "DataArray does not match a known spatial loader signature"),
            ),
            None,
            id="no_loader",
        ),
        pytest.param(  # Bad load - catching corrupted spatial loader signatures
            DataArray(
                data=np.array(np.arange(9)),
                coords={"z": np.arange(9)},
                name="should_not_work",
            ),
            False,
            "air_temperature",
            pytest.raises(AttributeError),
            (
                (INFO, "Adding data array for 'should_not_work'"),
                (
                    CRITICAL,
                    "Data array maps to unknown spatial loader 'does_not_exist'",
                ),
            ),
            None,
            id="invalid_loader_mapping",
        ),
        pytest.param(  # Valid load from square_xy_coords
            DataArray(
                data=np.array([[0, 1], [2, 3]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="air_temperature",
            ),
            False,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            [0, 1, 2, 3],
            id="valid_square_xy_coords",
        ),
        pytest.param(  # Bad load - variable already exists
            DataArray(
                data=np.array([[0, 1], [2, 3]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="existing_var",
            ),
            False,
            "existing_var",
            pytest.raises(KeyError),
            (
                (
                    CRITICAL,
                    "Data array for 'existing_var' already loaded. Use replace=True",
                ),
            ),
            [0, 1, 2, 3],
            id="existing_var",
        ),
        pytest.param(  # Replacing previous load from square_xy_coords
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="existing_var",
            ),
            True,
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
            False,
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
            False,
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
            False,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Adding data array for 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_any_cell_id_dims",
        ),
    ],
)
def test_Data_load_dataarray(
    caplog, fixture_data, darray, replace, exp_name, exp_err, exp_log, exp_vals
):
    """Test the load_dataarray method.

    Note that fixture_data is edited to create existing variables and to provide an
    example of a corrupt spatial loader.
    """

    with exp_err:
        fixture_data.load_dataarray(darray, replace=replace)
        assert exp_name in fixture_data
        assert np.allclose(fixture_data[exp_name].values, exp_vals)

    # Check the error reports
    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames=["name", "replace", "exp_error", "exp_msg", "exp_log"],
    argvalues=[
        pytest.param(
            None,
            False,
            does_not_raise(),
            None,
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
            ),
            id="simple_load",
        ),
        pytest.param(
            "temperature",
            False,
            does_not_raise(),
            None,
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Renaming file variable 'temp' as 'temperature'"),
                (INFO, "Adding data array for 'temperature'"),
            ),
            id="load_with_rename",
        ),
        pytest.param(
            # Unusual doubled quotes in error message specifically required with
            # str(KeyError). See: https://stackoverflow.com/questions/24998968
            "existing_var",
            False,
            pytest.raises(KeyError),
            "\"Data array for 'existing_var' already loaded. Use replace=True\"",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Renaming file variable 'temp' as 'existing_var'"),
                (
                    CRITICAL,
                    "Data array for 'existing_var' already loaded. Use replace=True",
                ),
            ),
            id="load_with_clash",
        ),
        pytest.param(
            "existing_var",
            True,
            does_not_raise(),
            None,
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Renaming file variable 'temp' as 'existing_var'"),
                (INFO, "Replacing data array for 'existing_var'"),
            ),
            id="load_and_replace",
        ),
    ],
)
def test_Data_load_from_file_naming(
    caplog, datadir, name, replace, exp_error, exp_msg, exp_log
):
    """Test the coding of the name handling and replacement."""

    # Setup a Data instance to match the example files generated in test_data/

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    grid = Grid(
        grid_type="square",
        cell_nx=10,
        cell_ny=10,
        cell_area=10000,
        xoff=500000,
        yoff=200000,
    )
    data = Data(grid)

    # (Crudely) create an existing variable to test replacement
    data.data["existing_var"] = None

    datafile = datadir / "cellid_dims.nc"

    with exp_error as err:

        data.load_from_file(file=datafile, file_var="temp", name=name, replace=replace)

        # Check the naming has worked and the data are loaded
        datakey = name or "temp"
        assert datakey in data
        assert data[datakey].sum() == (20 * 100)

    if err:
        assert str(err.value) == exp_msg

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
            id="spld_cellid_dim_any",
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
            id="spld_cellid_dim_any_too_few",
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
            id="spld_cellid_dim_any_too_many",
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
            id="spld_cellid_coords_any",
        ),
        pytest.param(
            ["__any__"],
            "cellid_coords_too_few.nc",
            pytest.raises(ValueError),
            "The data cell ids are not a superset of grid cell ids.",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
                (CRITICAL, "The data cell ids are not a superset of grid cell ids."),
            ),
            None,
            id="spld_cellid_coords_any_too_few",
        ),
        pytest.param(
            ["__any__"],
            "cellid_coords_bad_cellid.nc",
            pytest.raises(ValueError),
            "The data cell ids are not a superset of grid cell ids.",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
                (CRITICAL, "The data cell ids are not a superset of grid cell ids."),
            ),
            None,
            id="spld_cellid_coords_any_bad_cellid",
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
            id="spld_xy_dim_square",
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
            id="spld_xy_dim_square_small",
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
            id="spld_xy_coords_square",
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
            id="spld_xy_coords_square_small",
        ),
        pytest.param(
            ["square"],
            "xy_coords_shifted.nc",
            pytest.raises(ValueError),
            "Mapped points do not cover all cells.",
            (
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Adding data array for 'temp'"),
                (CRITICAL, "Mapped points do not cover all cells."),
            ),
            None,
            id="spld_xy_coords_square_shifted",
        ),
    ],
)
@pytest.mark.parametrize(
    # On request, use the fixture to provide different grids
    "fixture_load_data_grids",
    ["square", "hexagon"],
    indirect=True,
)
def test_Data_load_from_file_data_handling(
    caplog,
    fixture_load_data_grids,
    supported_grids,
    datadir,
    filename,
    exp_error,
    exp_msg,
    exp_log,
    exp_sum_val,
):
    """Test the loading of data from file formats against various grids.

    This tests the data handling, and test_Data_load_from_file_naming handles the data
    name and name replacement functionality
    """

    # Setup a Data instance to match the example files generated in test_data/

    from virtual_rainforest.core.data import Data

    # Skip combinations where loader does not supported this grid
    if not (
        ("__any__" in supported_grids)
        or (fixture_load_data_grids.grid_type in supported_grids)
    ):
        pytest.skip("Combination not tested")

    data = Data(fixture_load_data_grids)
    datafile = datadir / filename

    with exp_error as err:

        data.load_from_file(file=datafile, file_var="temp")

        # Check the data is in fact loaded and that a simple sum of values matches
        assert "temp" in data
        assert data["temp"].sum() == exp_sum_val

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)

    return


@pytest.mark.parametrize(
    argnames=[
        "file",
        "exp_error",
        "exp_msg",
        "exp_log",
    ],
    argvalues=[
        pytest.param(
            "test.toml",
            does_not_raise(),
            None,
            (
                (INFO, "Loading data from configuration"),
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Renaming file variable 'temp' as 'temp_1'"),
                (INFO, "Adding data array for 'temp_1'"),
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Renaming file variable 'temp' as 'temp_2'"),
                (INFO, "Adding data array for 'temp_2'"),
                (INFO, "Loading variable 'temp' from file:"),
                (INFO, "Renaming file variable 'temp' as 'temp_3'"),
                (INFO, "Adding data array for 'temp_3'"),
            ),
            id="valid config",
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
    caplog, datadir, fixture_load_data_grids, file, exp_error, exp_msg, exp_log
):
    """Test the loading of data configuration strings.

    TODO - think about a better way to do this.

    1. Could run with actual files at known and fixed paths to be portable across test
       systems.
    2. Could mock Data.load_from_file to avoid needing real files and just test the
       cofig loader part of the mechanism
    """

    # Setup a Data instance to match the example files generated in test_data/

    from virtual_rainforest.core.config import load_in_config_files
    from virtual_rainforest.core.data import Data

    # Skip combinations where loader does not supported this grid
    data = Data(fixture_load_data_grids)
    file = [datadir / file]

    with exp_error as err:
        cfg = load_in_config_files(file)

    # Edit the paths loaded
    for each_var in cfg["core"]["data"]["variable"]:
        each_var["file"] = datadir / each_var["file"]

    data.load_data_config(data_config=cfg["core"]["data"])

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)
