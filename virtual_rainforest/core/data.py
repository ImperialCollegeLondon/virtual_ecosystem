"""API documentation for the :mod:`core.data` module.
**************************************************

This module handles the population and storage of data sources used to run Virtual
Rainforest simulations.

The Data class
==============

The core :class:`~virtual_rainforest.core.data.Data` class is a wrapper around an
:class:`~xarray.DataSet` object, which is used to core variables in the simulation on
shared axes. The :class:`~xarray.DataSet` object is stored as the :attr:`Data.data`
attribute, and this attribute can be used directly to access :class:`~xarray.DataSet`
methods.

The :class:`~virtual_rainforest.core.data.Data` itself provides methods to add data to
an instance, and to automatically validate added data against the configuration of the
simulation.

* The :class:`~virtual_rainforest.core.data.Data.__setitem__` method is used to validate
  input data. The data must be an :class:`~xarray.DataSet` object and it is then checked
  to see that its dimensions are congruent with the simulation configuration. Valid
  inputs are then added onto the internal :class:`~xarray.DataSet` instance.
* The :class:`~virtual_rainforest.core.data.Data.__getitem__` method is used to retrieve
  a named variable from the internal :class:`~xarray.DataSet` instance.
* The :class:`~virtual_rainforest.core.data.Data.__contains__` method is provided to
  test if a named variable is included in the internal :class:`~xarray.DataSet`
  instance.

.. code-block:: python

    grid = Grid()
    data = Data(grid)
    data['varname'] = DataArray([1,2,3])
    'varname' in data
    data['varname']

Data validation
---------------

The :meth:`~virtual_rainforest.core.data.Data.__setitem__` method  validates a
provided :class:`~xarray.DataArray` by passing it to the
:func:`~virtual_rainforest.core.axes.validate_datarray` function, described in the
:mod:`~virtual_rainforest.core.axes` module. See that module for discussion of the
:class:`~virtual_rainforest.core.axes.AxisValidators` class and the concept of core
axes.

The :class:`~virtual_rainforest.core.data.Data` instance records validation that has
been applied to each variable on each core axis and provides the
:class:`~virtual_rainforest.core.data.Data.on_core_axis` method to allow models to
confirm that required variables have been validated on particular axes.

Adding data from a file
-----------------------

The general solution for programmatically adding data from a file is to:

* manually open a data file using the appropriate reader packages for the format,
* coerce the data into a properly structured :class:`~xarray.DataArray` object, and then
* use the :meth:`~virtual_rainforest.core.data.Data.__setitem__` method to validate and
  add it to a :class:`~virtual_rainforest.core.data.Data` instance.

The  :meth:`~virtual_rainforest.core.data.Data.load_from_file` method implements this
general recipe for known file formats, with readers described
:class:`~virtual_rainforest.core.readers` module. See the details of that module for
supported formats and for extending the system to additional file formats.

Using a data configuration
--------------------------

A :class:`~virtual_rainforest.core.data.Data` instance can also be populated using the
:meth:`~virtual_rainforest.core.data.Data.load_from_config` method. This is expecting to
take a properly validated configuration dictionary, typically loaded from a TOML file
during configuration (see :class:`~virtual_rainforest.core.config`). The expected
structure is as follows:

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
arguments for :meth:`~virtual_rainforest.core.data.Data.load_from_file`. Data
configurations must not contain repeated data variable names.  The ``data_var_name`` is
optional and is used to change the variable name used in the file to a different value
to be used within the simulation.
"""  # noqa: D205

from pathlib import Path
from typing import Any, Optional

import numpy as np
from xarray import DataArray, Dataset

from virtual_rainforest.core.axes import AXIS_VALIDATORS, validate_dataarray
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
        grid: The Grid instance that will be used for simulation.
    """

    def __init__(self, grid: Grid) -> None:

        # Set up the instance properties
        if not isinstance(grid, Grid):
            log_and_raise("Data must be initialised with a Grid object", TypeError)

        self.grid: Grid = grid
        """The configured Grid to be used in a simulation."""
        self.data = Dataset()
        """The :class:`~xarray.Dataset` used to store data."""
        self._variable_validation: dict[str, dict[str, Optional[str]]] = {}
        """Private attribute used to record validation details for loaded variables."""

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

        # Validate and store the data array
        value, valid_dict = validate_dataarray(value=value, grid=self.grid)
        self.data[key] = value
        self._variable_validation[key] = valid_dict

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

    def on_core_axis(self, var_name: str, axis_name: str) -> bool:
        """Check core axis validation.

        This function checks if a given variable loaded into a Data instance has been
        validated on one of the core axes.

        Args:
            var_name: The name of a variable
            axis_name: The core axis name

        Returns:
            A boolean indicating if the variable was validated on the named axis.

        Raises:
            ValueError: Unknown variable or core axis name
            RuntimeError: Incomplete variable validation data in Data instance.
        """

        if var_name not in self.data:
            raise ValueError(f"Unknown variable name: {var_name}")

        if var_name not in self._variable_validation:
            raise RuntimeError(f"Missing variable validation data: {var_name}")

        if axis_name not in AXIS_VALIDATORS:
            raise ValueError(f"Unknown core axis name: {axis_name}")

        return False if self._variable_validation[var_name][axis_name] is None else True

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
        value = loader(file, file_var_name)

        # Replace the file variable name if requested
        if data_var_name is not None:
            LOGGER.info(
                "Renaming file variable '%s' as '%s'", value.name, data_var_name
            )
            value.name = data_var_name

        # Add the data array, note that the __setitem__ method here does the actual
        # validation required for this step.
        self[value.name] = value

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
                        file=Path(each_var["file"]),
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


class DataGenerator:
    """Generate artificial data.

    Currently just a signature sketch.
    """

    def __init__(
        self,
        # grid: GRID,
        spatial_axis: str,
        temporal_axis: str,
        temporal_interpolation: np.timedelta64,
        seed: Optional[int],
        method: str,  # one of the numpy.random.Generator methods
        **kwargs: Any,
    ) -> None:

        pass
