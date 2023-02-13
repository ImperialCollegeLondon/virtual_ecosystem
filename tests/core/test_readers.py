"""Testing the data loaders."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, INFO

import pytest
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
    """Tests the file format loader decorator.

    TODO - Note that the test here is actually changing the live DATA_LOADER_REGISTRY,
           so that the tests are not independent of one another.
    """

    # Import register_data_loader - this triggers the registration of existing data
    # loaders so need to clear those log messages before trying new ones
    from virtual_rainforest.core.logger import LOGGER
    from virtual_rainforest.core.readers import register_file_format_loader

    # Capture debug/setup messages
    LOGGER.setLevel("DEBUG")

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
def test_load_netcdf(shared_datadir, caplog, file, file_var, exp_err, expected_log):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.readers import load_netcdf

    with exp_err:
        darray = load_netcdf(shared_datadir / file, file_var)
        assert isinstance(darray, DataArray)

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
            ((INFO, "Loading variable 'temp' from file:"),),
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

    from virtual_rainforest.core.readers import load_to_dataarray

    datafile = shared_datadir / filename

    with exp_error as err:
        dataarray = load_to_dataarray(file=datafile, var_name="temp")

        # Check the data is in fact loaded and that a simple sum of values matches
        dataarray.sum() == exp_sum_val

    if err:
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)
