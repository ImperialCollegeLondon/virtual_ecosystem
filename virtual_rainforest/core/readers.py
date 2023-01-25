"""API documentation for the :mod:`core.readers` module.
*****************************************************

This module handles the registration of functions to read files from different formats
and convert them into :class:`~xarray.DataArray` objects.

The FILE_FORMAT_REGISTRY
========================

The :attr:`~virtual_rainforest.core.data.FILE_FORMAT_REGISTRY` is used to register the
set of known file formats for use in
:meth:`~virtual_rainforest.core.data.Data.load_from_file`. This registry is extendable,
so that new functions that implement data loading for a given file format can be
added to those supported by :meth:`~virtual_rainforest.core.data.Data.load_from_file`.

New file format readers are made available using the
:func:`~virtual_rainforest.core.data.register_file_format_loader` decorator, which needs
to specify the file formats supported (as a tuple of file suffixes) and then decorate a
function that returns a :class:`~xarray.DataArray` suitable for validation using
:func:`~virtual_rainforest.core.axes.validate_dataarray`. For
example:

.. code-block:: python

    @register_file_format_loader(('.tif', '.tiff'))
    def new_function_to_load_tif_data(...):
        # code to turn tif file into a data array
"""  # noqa: D205

from pathlib import Path
from typing import Callable, Optional

from xarray import DataArray, load_dataset

from virtual_rainforest.core.logger import LOGGER, log_and_raise

FILE_FORMAT_REGISTRY: dict[str, Callable] = {}
"""A registry for different file format loaders

This dictionary maps a tuple of file format suffixes onto a function that allows the
data to be loaded. That loader function should coerce the data into an xarray DataArray.

Users can register their own functions to load from a particular file format using the
:func:`~virtual_rainforest.core.data.register_file_format_loader` decorator. The
function itself should have the following signature:

.. code-block:: python

    func(file: Path, file_var: str) -> DataArray

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
def load_netcdf(file: Path, file_var_name: str) -> DataArray:
    """Loads a DataArray from a NetCDF file.

    Args:
        file: A Path for a NetCDF file containing the variable to load.
        file_var_name: A string providing the name of the variable in the file.
    """

    # Note that this deliberately doesn't contain any INFO logging messages to maintain
    # a simple logging sequence - load_from_file, load_dataarray - without unnecessary
    # logger noise about the specific format unless there is an exception.

    # Try and load the provided file
    try:
        dataset = load_dataset(file)
    except FileNotFoundError:
        log_and_raise(f"Data file not found: {file}", FileNotFoundError)
    except ValueError as err:
        log_and_raise(f"Could not load data from {file}: {err}.", ValueError)

    # Check if file var is in the dataset
    if file_var_name not in dataset:
        log_and_raise(f"Variable {file_var_name} not found in {file}", KeyError)

    return dataset[file_var_name]


def load_to_dataarray(
    file: Path,
    file_var_name: str,
    data_var_name: Optional[str] = None,
) -> DataArray:
    """Loads data from a file into a DataArray.

    The function takes a path to a file format supported in the
    :attr:`~virtual_rainforest.core.readers.FILE_FORMAT_REGISTRY` and uses the
    appropriate data loader function to load the data and convert it to a
    {class}`~xarray.DataArray`, ready for insertion into a
    :attr:`~virtual_rainforest.core.data.Data` instance.

    Args:
        file: A Path for the file containing the variable to load.
        file_var_name: A string providing the name of the variable in the file.
        data_var_name: An optional replacement name to use as the data key in the
            Data instance.
    """

    # Detect file type
    file_type = file.suffix

    # Can the data mapper handle this grid and file type combination?
    if file_type not in FILE_FORMAT_REGISTRY:
        log_and_raise(f"No file format loader provided for {file_type}", ValueError)

    # If so, load the data
    LOGGER.info("Loading variable '%s' from file: %s", file_var_name, file)
    loader = FILE_FORMAT_REGISTRY[file_type]
    value = loader(file, file_var_name)

    # Replace the file variable name if requested
    if data_var_name is not None:
        LOGGER.info("Renaming file variable '%s' as '%s'", value.name, data_var_name)
        value.name = data_var_name

    return value
