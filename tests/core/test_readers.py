"""Testing the data loaders."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, INFO
from zipfile import BadZipFile

import pytest
from pandas.errors import ParserError
from xarray import DataArray

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames=["file_types", "expected_log"],
    argvalues=[
        (  # Single file type - add and replace
            (".xyz",),
            ((DEBUG, "Adding data loader function for .xyz"),),
        ),
        (
            (".ghi",),
            ((DEBUG, "Replacing existing data loader function for .ghi"),),
        ),
        (  # Tuple of file types, add only
            (".abc", ".def"),
            (
                (DEBUG, "Adding data loader function for .abc"),
                (DEBUG, "Adding data loader function for .def"),
            ),
        ),
        (  # Tuple of file types, add and replace
            (".jkl", ".ghi"),
            (
                (DEBUG, "Adding data loader function for .jkl"),
                (DEBUG, "Replacing existing data loader function for .ghi"),
            ),
        ),
    ],
)
def test_file_format_loader(caplog, file_types, expected_log):
    """Tests the file format loader decorator."""

    # Import register_data_loader - this triggers the registration of existing data
    # loaders so need to clear those log messages before trying new ones
    from virtual_ecosystem.core.readers import register_file_format_loader

    # Create an existing one to test replace modes
    @register_file_format_loader(file_types=".ghi")
    def existing_func():
        return

    caplog.clear()

    # Decorate a mock function to test the failure modes
    @register_file_format_loader(file_types=file_types)
    def test_func():
        return

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["file", "file_vars", "exp_err", "expected_log"],
    argvalues=[
        pytest.param(
            "not_there.nc",
            ["irrelevant"],
            pytest.raises(FileNotFoundError),
            ((CRITICAL, "Data file not found"),),
            id="file_missing",
        ),
        pytest.param(
            "garbage.nc",
            ["irrelevant"],
            pytest.raises(ValueError),
            ((CRITICAL, "Could not load data from"),),
            id="file_misformatted",
        ),
        pytest.param(
            "xy_dim.nc",
            ["missing"],
            pytest.raises(KeyError),
            ((CRITICAL, "Data variables not found in"),),
            id="missing_var",
        ),
        pytest.param(
            "xy_dim.nc",
            ["air_temperature"],
            does_not_raise(),
            (),
            id="all_good_single_var",
        ),
        pytest.param(
            "cellid_coords.nc",
            ["air_temperature", "precipitation", "elevation"],
            does_not_raise(),
            (),
            id="all_good_multi_var",
        ),
        pytest.param(
            "cellid_coords.nc",
            ["air_temperature", "precipitation", "elves_station"],
            pytest.raises(KeyError),
            ((CRITICAL, "Data variables not found in"),),
            id="missing_multi_var",
        ),
    ],
)
def test_load_netcdf(shared_datadir, caplog, file, file_vars, exp_err, expected_log):
    """Test the netdcf variable loader."""

    from virtual_ecosystem.core.readers import load_netcdf

    caplog.clear()

    with exp_err:
        result = load_netcdf(shared_datadir / file, file_vars)
        assert len(result) == len(file_vars)
        assert list(result.keys()) == file_vars
        for ky, val in result.items():
            assert isinstance(val, DataArray)

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["file", "file_vars", "exp_err", "expected_log"],
    argvalues=[
        pytest.param(
            "not_there.csv",
            ["irrelevant"],
            pytest.raises(FileNotFoundError),
            ((CRITICAL, "Data file not found"),),
            id="file_missing",
        ),
        pytest.param(
            "garbage.csv",
            ["irrelevant"],
            pytest.raises(ParserError),
            ((CRITICAL, "Could not load data from"),),
            id="file_malformatted",
        ),
        pytest.param(
            "reader_test.csv",
            ["missing"],
            pytest.raises(KeyError),
            ((CRITICAL, "Data variables not found in"),),
            id="missing_var",
        ),
        pytest.param(
            "reader_test.csv",
            ["var1"],
            does_not_raise(),
            (),
            id="all_good_single_var",
        ),
        pytest.param(
            "reader_test.csv",
            ["var1", "var2"],
            does_not_raise(),
            (),
            id="all_good_multi_var",
        ),
        pytest.param(
            "reader_test.csv",
            ["var1", "var22"],
            pytest.raises(KeyError),
            ((CRITICAL, "Data variables not found in"),),
            id="missing_multi_var",
        ),
    ],
)
def test_load_csv(shared_datadir, caplog, file, file_vars, exp_err, expected_log):
    """Test the netdcf variable loader."""

    from virtual_ecosystem.core.readers import load_csv

    caplog.clear()

    with exp_err:
        result = load_csv(shared_datadir / file, file_vars)
        assert len(result) == len(file_vars)
        assert list(result.keys()) == file_vars
        for ky, val in result.items():
            assert isinstance(val, DataArray)

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["file", "file_vars", "exp_err", "expected_log"],
    argvalues=[
        pytest.param(
            "not_there.xlsx",
            ["irrelevant"],
            pytest.raises(FileNotFoundError),
            ((CRITICAL, "Data file not found"),),
            id="file_missing",
        ),
        pytest.param(
            "garbage.xlsx",
            ["irrelevant"],
            pytest.raises(BadZipFile),
            ((CRITICAL, "Could not load data from"),),
            id="file_malformatted",
        ),
        pytest.param(
            "reader_test.xlsx",
            ["missing"],
            pytest.raises(KeyError),
            ((CRITICAL, "Data variables not found in"),),
            id="missing_var",
        ),
        pytest.param(
            "reader_test.xlsx",
            ["var1"],
            does_not_raise(),
            (),
            id="all_good_single_var",
        ),
        pytest.param(
            "reader_test.xlsx",
            ["var1", "var2"],
            does_not_raise(),
            (),
            id="all_good_multi_var",
        ),
        pytest.param(
            "reader_test.xlsx",
            ["var1", "var22"],
            pytest.raises(KeyError),
            ((CRITICAL, "Data variables not found in"),),
            id="missing_multi_var",
        ),
    ],
)
def test_load_excel(shared_datadir, caplog, file, file_vars, exp_err, expected_log):
    """Test the netdcf variable loader."""

    from virtual_ecosystem.core.readers import load_excel

    caplog.clear()

    with exp_err:
        result = load_excel(shared_datadir / file, file_vars)
        assert len(result) == len(file_vars)
        assert list(result.keys()) == file_vars
        for ky, val in result.items():
            assert isinstance(val, DataArray)

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=[
        "filename",
        "exp_error",
        "exp_msg",
        "exp_log",
        "exp_sum_val",
    ],
    argvalues=[
        pytest.param(
            "this_data_format.not_handled",
            pytest.raises(ValueError),
            "No file format loader provided for .not_handled",
            ((CRITICAL, "No file format loader provided for .not_handled"),),
            None,
            id="unhandled file format",
        ),
        pytest.param(
            "cellid_dims.nc",
            does_not_raise(),
            None,
            ((INFO, "Loading variables from file"),),
            20 * 100,
            id="valid_netcdf",
        ),
    ],
)
def test_load_to_dataarray(
    caplog,
    shared_datadir,
    filename,
    exp_error,
    exp_msg,
    exp_log,
    exp_sum_val,
):
    """Test the loading of data to dataarray.

    This is primarily about making sure that the registered loaders are called correctly
    and the test methods for individual readers should test failure modes.
    """

    # Setup a Data instance to match the example files generated in tests/core/data

    from virtual_ecosystem.core.readers import load_to_dataarray

    datafile = shared_datadir / filename

    with exp_error as err:
        results = load_to_dataarray(file=datafile, var_names=["air_temperature"])

        # Check the data is in fact loaded and that a simple sum of values matches
        assert "air_temperature" in results
        assert results["air_temperature"].sum() == exp_sum_val

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)
