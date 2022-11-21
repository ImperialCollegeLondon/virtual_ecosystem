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
            "two_dim_xy.nc",
            "missing",
            pytest.raises(KeyError),
            (
                (INFO, "Loading data from"),
                (CRITICAL, "Variable 'missing' not found in"),
            ),
        ),
        (
            "two_dim_xy.nc",
            "temp",
            does_not_raise(),
            (
                (INFO, "Loading data from"),
                (INFO, "Loaded variable 'temp' from "),
            ),
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
def test_any_cellid_dim_array(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, any_cellid_dim_array
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = any_cellid_dim_array(data, darray)
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
def test_any_cellid_coord_array(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, any_cellid_coord_array
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = any_cellid_coord_array(data, darray)

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
def test_square_xy_dim_array(caplog, grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, square_xy_dim_array
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = square_xy_dim_array(data, darray)
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
def test_square_xy_coords_array(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.data import Data, square_xy_coord_array
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)
    data = Data(grid)

    with exp_err as excep:
        darray = square_xy_coord_array(data, darray)
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
        "dname",
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
            None,
            False,
            "air_temperature",
            pytest.raises(ValueError),
            ((CRITICAL, "Cannot add DataArray with unnamed variable"),),
            None,
            id="missing_name",
        ),
        pytest.param(  # Bad load - no known loader
            DataArray(
                data=np.array(np.arange(9)),
                coords={"nope": np.arange(9)},
                name="should_not_work",
            ),
            None,
            False,
            "air_temperature",
            pytest.raises(ValueError),
            (
                (INFO, "Data: loading 'should_not_work'"),
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
            None,
            False,
            "air_temperature",
            pytest.raises(AttributeError),
            (
                (INFO, "Data: loading 'should_not_work'"),
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
            None,
            False,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Data: loading 'air_temperature'"),),
            [0, 1, 2, 3],
            id="valid_square_xy_coords",
        ),
        pytest.param(  # Bad load - variable already exists
            DataArray(
                data=np.array([[0, 1], [2, 3]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="existing_var",
            ),
            None,
            False,
            "existing_var",
            pytest.raises(KeyError),
            ((CRITICAL, "Data: 'existing_var' already loaded. Use replace=True"),),
            [0, 1, 2, 3],
            id="existing_var",
        ),
        pytest.param(  # Replacing previous load from square_xy_coords
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="existing_var",
            ),
            None,
            True,
            "existing_var",
            does_not_raise(),
            ((INFO, "Data: replacing 'existing_var'"),),
            [4, 5, 6, 7],
            id="replacing_data",
        ),
        pytest.param(  # Filling missing name
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                coords={"y": [2, 1], "x": [1, 2]},
            ),
            "air_temperature",
            True,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Data: loading 'air_temperature'"),),
            [4, 5, 6, 7],
            id="providing_name",
        ),
        pytest.param(  # Overriding dataarray name
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                coords={"y": [2, 1], "x": [1, 2]},
                name="name_not_to_be_used",
            ),
            "air_temperature",
            True,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Data: loading 'air_temperature'"),),
            [4, 5, 6, 7],
            id="overriding_name",
        ),
        pytest.param(  # Good load from square_xy_dims
            DataArray(
                data=np.array([[4, 5], [6, 7]]),
                dims=("y", "x"),
                name="air_temperature",
            ),
            None,
            False,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Data: loading 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_square_xy_dims",
        ),
        pytest.param(  # Good load from any_cellid_coords
            DataArray(
                data=np.array([4, 5, 6, 7]),
                coords={"cell_id": [0, 1, 2, 3]},
                name="air_temperature",
            ),
            None,
            False,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Data: loading 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_any_cellid_coords",
        ),
        pytest.param(  # Good load from any_cellid_dim
            DataArray(
                data=np.array([4, 5, 6, 7]),
                dims=("cell_id",),
                name="air_temperature",
            ),
            None,
            False,
            "air_temperature",
            does_not_raise(),
            ((INFO, "Data: loading 'air_temperature'"),),
            [4, 5, 6, 7],
            id="load_any_cell_id_dims",
        ),
    ],
)
def test_Data_load_dataarray(
    caplog, fixture_data, darray, dname, replace, exp_name, exp_err, exp_log, exp_vals
):
    """Test the load_dataarray method.

    Note that fixture_data is edited to create existing variables and to provide an
    example of a corrupt spatial loader.
    """

    with exp_err:
        fixture_data.load_dataarray(darray, name=dname, replace=replace)
        assert exp_name in fixture_data
        assert np.allclose(fixture_data[exp_name].values, exp_vals)

    # Check the error reports
    log_check(caplog, exp_log)


# @pytest.mark.parametrize(
#     argnames=["data_cfg", "expected_log"],
#     argvalues=[
#         (
#             {"variable": [{"file_var": "x", "file": "/path/to/unknown/format.xyz"}]},
#             (
#                 (INFO, "Loading data from file: /path/to/unknown/format.xyz"),
#                 (ERROR, "No data loader provided for .xyz files and square grids"),
#             ),
#         ),
#     ],
# )
# def test_setup_data(caplog, fixture_square_grid, data_cfg, expected_log):
#     """Tests the setup_data high level function."""
#     from virtual_rainforest.core.data import setup_data

#     setup_data(data_config=data_cfg, grid=fixture_square_grid)

#     log_check(caplog, expected_log)


# @pytest.mark.parametrize(
#     argnames=["filename", "expected_outcome", "expected_outcome_msg"],
#     argvalues=[
#         pytest.param("two_dim_xy.nc", does_not_raise(), "None", id="two_dim_xy"),
#         pytest.param(
#             "two_dim_xy_6by10.nc",
#             pytest.raises(ValueError),
#             "Data xy dimensions do not match grid",
#             id="two_dim_xy_6by10",
#         ),
#         pytest.param(
#             "two_dim_xy_lowx.nc",
#             pytest.raises(ValueError),
#             "Data coordinates do not align with grid coordinates.",
#             id="two_dim_xy_lowx",
#         ),
#         pytest.param("two_dim_idx.nc", does_not_raise(), "None", id="two_dim_idx"),
#         pytest.param(
#             "two_dim_idx_6by10.nc",
#             pytest.raises(ValueError),
#             "Data xy dimensions do not match grid",
#             id="two_dim_idx_6by10",
#         ),
#         pytest.param(
#             "one_dim_cellid.nc", does_not_raise(), "None", id="one_dim_cellid"
#         ),
#         pytest.param(
#             "one_dim_cellid_lown.nc",
#             pytest.raises(ValueError),
#             "Grid defines 100 cells, data provides 60",
#             id="one_dim_cellid_lown",
#         ),
#         pytest.param(
#             "one_dim_points_xy.nc", does_not_raise(), "None", id="one_dim_points_xy"
#         ),
#         pytest.param(
#             "one_dim_points_xy_xney.nc",
#             pytest.raises(ValueError),
#             "The cell_ids in the data do not match grid cell ids.",
#             id="one_dim_points_xy_xney",
#         ),
#         pytest.param(
#             "one_dim_cellid_badid.nc",
#             pytest.raises(ValueError),
#             "The x and y data have different dimensions",
#             id="one_dim_cellid_badid",
#         ),
#         pytest.param(
#             "one_dim_points_order_only.nc",
#             does_not_raise(),
#             "None",
#             id="one_dim_points_order_only",
#         ),
#     ],
# )
# def test_map_dataset_onto_square_grid(
#     fixture_square_grid, datadir, filename, expected_outcome, expected_outcome_msg
# ):
#     """Test ability to map NetCDF files.

#     The test parameters include both passing and failing files, stored in test_data.
#     """
#     from virtual_rainforest.core.data import _square_xy_coord_array

#     datafile = os.path.join(datadir, filename)
#     dataset = load_dataset(datafile)

#     with expected_outcome as outcome:

#         _square_xy_coord_array(fixture_square_grid, dataset)

#         assert str(outcome) == expected_outcome_msg
