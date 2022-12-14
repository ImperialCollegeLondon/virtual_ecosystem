"""API documentation for the :mod:`core.data` module.
************************************************** # noqa: D205

This module handles the population and storage of data sources used to run Virtual
Rainforest simulations.

The Data class
==============

The core :class:`~virtual_rainforest.core.data.Data` class is a dictionary-like object
that can be used to access data simply as ``data['var_name']``. All of the entries in
the dictionary are :class:`~xarray.DataArray` objects, which provides a flexible
indexing system onto underlying :mod:`numpy` arrays. A
:class:`~virtual_rainforest.core.data.Data` instance is initalised using the core
configuration parameters for a simulation, currently a
:class:`~virtual_rainforest.core.grid.Grid`. The ``__getitem__`` method is provided to
make it easy to access data using the variable name as a key, but the ``__setitem__``
method is deliberately disabled. Data must be added to a
:class:`~virtual_rainforest.core.data.Data` instance using the
:meth:`~virtual_rainforest.core.data.Data.load_dataarray` method.

..code-block:: python

    grid = Grid()
    data = Data(grid)
    # Not this
    data['varname'] = DataArray([1,2,3])
    # But this
    data.load_dataarray(DataArray([1,2,3], name='varname'))

Adding data to a Data instance
------------------------------

The :meth:`~virtual_rainforest.core.data.Data.load_dataarray` method validates a
provided :class:`~xarray.DataArray` using a configurable system of axis validation
methods (:mod:`~virtual_rainforest.core.axes`),  before the data is added  to a
:class:`~virtual_rainforest.core.data.Data` instance. These validators are used to check
that particular signatures of dimensions and coordinates in the provided
:class:`~xarray.DataArray` are congruent with the core configuration parameters.

Adding data from a file
-----------------------

The general solution for programmatically adding data from a file is to:

* manually open a data file using the appropriate reader packages for the format,
* coerce the data into a properly structured :class:`~xarray.DataArray` object, and then
* use the :class:`~virtual_rainforest.core.data.Data.load_dataarray` method.

However, the :meth:`~virtual_rainforest.core.data.Data.load_from_file` method
automatically loads data from known formats defined in the
:attr:`~virtual_rainforest.core.data.FILE_FORMAT_REGISTRY`.

Using a data configuration
--------------------------

A :class:`~virtual_rainforest.core.data.Data` instance can also be populated using the
:meth:`~virtual_rainforest.core.data.Data.load_from_config` method. This is expecting to
take a properly validated configuration dictionary, loaded from a TOML file that
specifies data source files, where `data_var_name` is optional and is used to store the
data in a `Data` instance under a different variable name to the name used in the file.

.. code-block:: toml

    [[core.data.variable]]
    file="/path/to/file.nc"
    file_var_name="precip"
    data_var_name="precipitation"
    [[core.data.variable]]
    file="/path/to/file.nc"
    file_var_name="temperature"
    [[core.data.variable]]
    file="/path/to/file.csv"
    file_var_name="elev"
    data_var_name="elevation"

Note that the properties for each variable in the configuration file are just the
arguments for :meth:`~virtual_rainforest.core.data.Data.load_from_file`. Note that data
configurations cannot define repeated variable names.
"""

from pathlib import Path
from typing import Any, Optional

from xarray import DataArray, Dataset

from virtual_rainforest.core.config import ConfigurationError
from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.readers import FILE_FORMAT_REGISTRY


class Data:
    """The Virtual Rainforest data object.

    This class holds data for a Virtual Rainforest simulation. It functions like a
    dictionary but the class extends the dictionary methods to provide common methods
    for data validation etc and to hold key attributes, such as the underlying spatial
    grid.

    Args:
        grid: A Grid instance that loaded datasets with spatial structure must match.

    Attrs:
        grid: The grid instance
    """

    def __init__(self, grid: Grid) -> None:

        # Set up the instance properties
        if not isinstance(grid, Grid):
            log_and_raise("Data must be initialised with a Grid object", TypeError)

        self.grid = grid
        self.data = Dataset()

    def __repr__(self) -> str:
        """Returns a representation of a Data instance."""

        if self.data:
            return f"Data: {list(self.data.data_vars)}"

        return "Data: no variables loaded"

    def __setitem__(self, key: str, value: DataArray) -> None:
        """Load a data array into a Data instance.

        This method takes an input DataArray object and then matches the dimension and
        coordinates signature of the array to find a loading routines given the grid
        used in the Data instance. That routine is used to validate the DataArray and
        then add the DataArray to the Data dictionary or replace the existing DataArray
        under that key.

        Note that the DataArray name is expected to match the standard internal variable
        names used in Virtual Rainforest.

        Args:
            key: The name to store the data under
            value: The DataArray to be stored
        """

        # Import core.axis functions here to avoid circular imports
        from virtual_rainforest.core.axes import AXIS_VALIDATORS, get_validator

        if not isinstance(value, DataArray):
            log_and_raise(
                "Only DataArray objects can be added to Data instances", TypeError
            )

        # Ensure dataarray name matches the key
        value.name = key

        if key not in self.data.data_vars:
            LOGGER.info(f"Adding data array for '{key}'")
        else:
            LOGGER.info(f"Replacing data array for '{key}'")

        # Look for data validators on registered axes
        for axis in AXIS_VALIDATORS.keys():

            axis_validator_func = get_validator(axis=axis, data=self, darray=value)

            if axis_validator_func is None:
                # Record the lack of a validator for this axis
                value.attrs[axis] = None
            else:
                # Now run the validator using a broad base exception for now to reraise
                # upstream exceptions.
                try:
                    value = axis_validator_func(darray=value, grid=self.grid)
                except Exception as excep:
                    log_and_raise(str(excep), type(excep))

                # Record the axis validator to show this axis has been validated
                value.attrs[axis] = axis_validator_func.__name__

        # Store the data in the Dataset
        self.data[key] = value

    def __getitem__(self, key: str) -> DataArray:
        """Get a given data variable from a Data instance.

        This method looks for the provided key in the data variables saved in the `data`
        attribute and returns the DataArray for that variable. Note that this is just a
        shortcut: ``data_instance['var']`` is the same as ``data_instance.data['var']``.

        Args:
            key: The name of the data variable to get

        Raises:
            KeyError: if the data variable is not present
        """

        return self.data[key]

    def __contains__(self, key: str) -> bool:
        """Check if a given data variable is present in a Data instance.

        This method provides the `var_name in data_instance` functionality for a Data
        instance. This is just a shortcut: ``var in data_instance`` is the same as
        ``var in data_instance.data``.

        Args:
            key: A data variable name
        """

        return key in self.data

    def load_from_file(
        self,
        file: Path,
        file_var_name: str,
        data_var_name: Optional[str] = None,
    ) -> None:
        """Adds a variable to the data object.

        This method is used to programatically populate a variable in a Data instance
        from a file. The appropriate data loader function is selected using the file
        suffix and the grid type used in the Data instance.

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
        input_data = loader(file, file_var_name)

        # Replace the file variable name if requested
        if data_var_name is not None:
            LOGGER.info(
                "Renaming file variable '%s' as '%s'", input_data.name, data_var_name
            )
            input_data.name = data_var_name

        # Add the data array
        self[input_data.name] = input_data

    def load_data_config(self, data_config: dict[str, Any]) -> None:
        """Setup the simulation data from a user configuration.

        This is a method is used to validate a provided user data configuration and
        populate the Data instance object from the provided data sources. The
        data_config dictionary can contain lists of variables under the following
        keys:

        * `variable`: These are data elements loaded from a provided file. Each element
          in the list should be a dictionary providing the path to the file ('file'),
          the name of the variable within the file ('file_var_name') and optionally a
          different variable name to be used internally ('data_var_name').
        * `constant`: TODO
        * `generator`: TODO

        Args:
            data_config: A data configuration dictionary
        """

        LOGGER.info("Loading data from configuration")

        # Track errors in loading multiple files from a configuration
        clean_load = True

        # Handle variables
        if "variable" in data_config:

            # Check what name the data will be saved under but do then carry on to check
            # for other loading problems
            data_var_names = [
                v.get("data_var_name") or v["file_var_name"]
                for v in data_config["variable"]
            ]
            dupl_names = set(
                [str(md) for md in data_var_names if data_var_names.count(md) > 1]
            )
            if dupl_names:
                LOGGER.critical("Duplicate variable names in data configuration.")
                clean_load = False

            # Load data from each data source
            for each_var in data_config["variable"]:

                # Attempt to load the file, trapping exceptions as critical logger
                # messages and defer failure until the whole configuration has been
                # processed
                try:
                    self.load_from_file(
                        file=each_var["file"],
                        file_var_name=each_var["file_var_name"],
                        data_var_name=each_var.get("data_var_name"),
                    )
                except Exception as err:
                    LOGGER.critical(str(err))
                    clean_load = False

        if "constant" in data_config:
            raise NotImplementedError("Data config for constants not yet implemented.")

        if "generator" in data_config:
            raise NotImplementedError("Data config for generators not yet implemented.")

        if not clean_load:
            raise ConfigurationError("Data configuration did not load cleanly")
