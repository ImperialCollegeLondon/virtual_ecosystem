"""Testing the data loaders."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG

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
            "test_data/garbage.nc",
            "irrelevant",
            pytest.raises(ValueError),
            ((CRITICAL, "Could not load data from"),),
        ),
        (
            "test_data/xy_dim.nc",
            "missing",
            pytest.raises(KeyError),
            ((CRITICAL, "Variable missing not found in"),),
        ),
        (
            "test_data/xy_dim.nc",
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
