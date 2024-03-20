"""The :mod:`~virtual_ecosystem.core.readers` module provides the function
:func:`~virtual_ecosystem.core.readers.load_to_dataarray`, which is used to load data
from a file and convert it into a :class:`~xarray.DataArray` object. The ``DataArray``
can then be added to a :class:`~virtual_ecosystem.core.data.Data` instance for use in a
Virtual Ecosystem simulation.

The module also supports the registration of different reader functions, used to convert
files in different storage formats into a ``DataArray``. The
:func:`~virtual_ecosystem.core.readers.load_to_dataarray` automatically uses an
appropriate reader based on the file suffix.

The FILE_FORMAT_REGISTRY
========================

The :attr:`~virtual_ecosystem.core.readers.FILE_FORMAT_REGISTRY` is used to register a
set of known file formats for use in
:func:`~virtual_ecosystem.core.readers.load_to_dataarray`. This registry is extendable,
so that new functions that implement data loading for a given file format can be added.

New file format readers are made available using the
:func:`~virtual_ecosystem.core.readers.register_file_format_loader` decorator, which
needs to specify the file formats supported (as a tuple of file suffixes) and then
decorates a function that returns a :class:`~xarray.DataArray` that can be added to a
:class:`~virtual_ecosystem.core.data.Data` instance and validated
using :func:`~virtual_ecosystem.core.axes.validate_dataarray`. For example:

.. code-block:: python

    @register_file_format_loader(('.tif', '.tiff'))
    def new_function_to_load_tif_data(...):
        # code to turn tif file into a data array
"""  # noqa: D205, D415

from collections.abc import Callable
from pathlib import Path

from xarray import DataArray, load_dataset

from virtual_ecosystem.core.logger import LOGGER

FILE_FORMAT_REGISTRY: dict[str, Callable] = {}
"""A registry for different file format loaders

This dictionary maps a tuple of file format suffixes onto a function that allows the
data to be loaded. That loader function should coerce the data into an xarray DataArray.

Users can register their own functions to load from a particular file format using the
:func:`~virtual_ecosystem.core.readers.register_file_format_loader` decorator. The
function itself should have the following signature:

.. code-block:: python

    func(file: Path, var_name: str) -> DataArray

"""


def register_file_format_loader(file_types: tuple[str]) -> Callable:
    """Adds a data loader function to the data loader registry.

    This decorator is used to register a function that loads data from a given file type
    and coerces it to a DataArray.

    Args:
        file_types: A tuple of strings giving the file type that the function will map
            onto the Grid. The strings should match expected file suffixes for the file
            type.
    """

    def decorator_file_format_loader(func: Callable) -> Callable:
        # Ensure file_type is an iterable
        if isinstance(file_types, str):
            _file_types = (file_types,)
        else:
            _file_types = file_types

        # Register the mapper function for each combination of grid type and file type
        for this_ft in _file_types:
            if this_ft in FILE_FORMAT_REGISTRY:
                LOGGER.debug(
                    "Replacing existing data loader function for %s",
                    this_ft,
                )
            else:
                LOGGER.debug(
                    "Adding data loader function for %s",
                    this_ft,
                )

            FILE_FORMAT_REGISTRY[this_ft] = func

        return func

    return decorator_file_format_loader


@register_file_format_loader(file_types=(".nc",))
def load_netcdf(file: Path, var_name: str) -> DataArray:
    """Loads a DataArray from a NetCDF file.

    Args:
        file: A Path for a NetCDF file containing the variable to load.
        var_name: A string providing the name of the variable in the file.

    Raises:
        FileNotFoundError: with bad file path names.
        ValueError: if the file data is not readable.
        KeyError: if the named variable is not present in the data.
    """

    # Note that this deliberately doesn't contain any INFO logging messages to maintain
    # a simple logging sequence without unnecessary logger noise about the specific
    # format unless there is an exception.
    to_raise: Exception

    # Try and load the provided file
    try:
        dataset = load_dataset(file)
    except FileNotFoundError:
        to_raise = FileNotFoundError(f"Data file not found: {file}")
        LOGGER.critical(to_raise)
        raise to_raise
    except ValueError as err:
        to_raise = ValueError(f"Could not load data from {file}: {err}.")
        LOGGER.critical(to_raise)
        raise to_raise

    # Check if file var is in the dataset
    if var_name not in dataset:
        to_raise = KeyError(f"Variable {var_name} not found in {file}")
        LOGGER.critical(to_raise)
        raise to_raise

    return dataset[var_name]


def load_to_dataarray(
    file: Path,
    var_name: str,
) -> DataArray:
    """Loads data from a file into a DataArray.

    The function takes a path to a file format supported in the
    :attr:`~virtual_ecosystem.core.readers.FILE_FORMAT_REGISTRY` and uses the
    appropriate data loader function to load the data and convert it to a
    {class}`~xarray.DataArray`, ready for insertion into a
    :attr:`~virtual_ecosystem.core.data.Data` instance.

    Args:
        file: A Path for the file containing the variable to load.
        var_name: A string providing the name of the variable in the file.

    Raises:
        ValueError: if there is no loader provided for the file format.
    """

    # Detect file type
    file_type = file.suffix

    # Can the data mapper handle this grid and file type combination?
    if file_type not in FILE_FORMAT_REGISTRY:
        to_raise = ValueError(f"No file format loader provided for {file_type}")
        LOGGER.critical(to_raise)
        raise to_raise

    # If so, load the data
    LOGGER.info("Loading variable '%s' from file: %s", var_name, file)
    loader = FILE_FORMAT_REGISTRY[file_type]
    value = loader(file, var_name)

    return value
