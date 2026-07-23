"""The :mod:`~virtual_ecosystem.core.data` module handles the population and storage of
data sources used to run Virtual Ecosystem simulations.

The Data class
==============

The core :class:`~virtual_ecosystem.core.data.Data` class is used to store data for the
variables used in a simulation. It can be used both for data from external sources - for
example, data used to set the initial environment or time series of inputs - and for
internal variables used in the simulation. The class behaves like a dictionary - so data
can be retrieved and set using ``data_object['varname']`` - but also provide validation
for data being added to the object.

All data added to the class is stored in a :class:`~xarray.Dataset` object, and data
extracted from the object will be a :class:`~xarray.DataArray`. The ``Dataset`` can also
be accessed directly using the :attr:`~virtual_ecosystem.core.data.Data.data` attribute
of the class instance to use any of the :class:`~xarray.Dataset` class methods.

When data is added to a :class:`~virtual_ecosystem.core.data.Data` instance, it is
automatically validated against the configuration of a simulation before being added to
the :attr:`~virtual_ecosystem.core.data.Data.data` attribute. The validation process
also stores information that allows models to can confirm that a given variable has been
successfully validated.

The core of the :class:`~virtual_ecosystem.core.data.Data` class is the
:meth:`~virtual_ecosystem.core.data.Data.__setitem__` method. This method provides the
following functionality:

* It allows a ``DataArray`` to be added to a :class:`~virtual_ecosystem.core.data.Data`
  instance using the ``data['varname'] = data_array`` syntax.
* It applies the validation step using the
  :func:`~virtual_ecosystem.core.axes.validate_dataarray` function. See the
  :mod:`~virtual_ecosystem.core.axes` module for the details of the validation process,
  including the :class:`~virtual_ecosystem.core.axes.AxisValidator` class and the
  concept of core axes.
* It inserts the data into the :class:`~xarray.Dataset` instance stored in the
  :attr:`~virtual_ecosystem.core.data.Data.data` attribute.
* Lastly, it records the data validation details in the
  :attr:`~virtual_ecosystem.core.data.Data.variable_validation` attribute.

The :class:`~virtual_ecosystem.core.data.Data` class also provides three shorthand
methods to get information and data from an instance.

* The :meth:`~virtual_ecosystem.core.data.Data.__contains__` method tests if a named
  variable is included in the internal :class:`~xarray.Dataset` instance.

    .. code-block:: python

        # Equivalent code 'varname' in data 'varname' in data.data

* The :meth:`~virtual_ecosystem.core.data.Data.__getitem__` method is used to retrieve
  a named variable from the internal :class:`~xarray.Dataset` instance.

    .. code-block:: python

        # Equivalent code data['varname'] data.data['varname']

* The :meth:`~virtual_ecosystem.core.data.Data.on_core_axis` method queries the
  :attr:`~virtual_ecosystem.core.data.Data.variable_validation` attribute to confirm
  that a named variable has been validated on a named axis.

    .. code-block:: python

        # Test that the temperature variable has been validated on the spatial axis
        data.on_core_axis('temperature', 'spatial')

Adding data from a file
-----------------------

The general solution for programmatically adding data from a file is to:

* manually open a data file using an appropriate reader packages for the format,
* coerce data from named variables into properly structured :class:`~xarray.DataArray`
  objects, and then
* use the :meth:`~virtual_ecosystem.core.data.Data.__setitem__` method to validate and
  add it to a :class:`~virtual_ecosystem.core.data.Data` instance.

The  :func:`~virtual_ecosystem.core.readers.load_to_dataarray` implements data loading
to a DataArray for some known file formats, using file reader functions described in the
:mod:`~virtual_ecosystem.core.readers` module. See the details of that module for
supported formats and for extending the system to additional file formats.

.. code-block:: python

    # Load temperature data from a supported file
    from virtual_ecosystem.core.readers import load_to_dataarray
    results = load_to_dataarray(
        '/path/to/supported/format.nc', var_names=['temperature']
    )
    data['temperature'] = results['temperature']

Using a data configuration
--------------------------

A :class:`~virtual_ecosystem.core.data.Data` instance can also be populated using the
:meth:`~virtual_ecosystem.core.data.Data.load_data_config` method. This is expecting to
take a properly validated configuration object, typically created from TOML files
(see :class:`~virtual_ecosystem.core.config_builder.ConfigurationLoader`). The expected
structure of the data configuration section within those TOML files is as follows:

.. code-block:: toml

    [[core.data.variable]]
    file_path="/path/to/file.nc"
    var_name="precip"
    [[core.data.variable]]
    file_path="/path/to/file.nc"
    var_name="temperature"
    [[core.data.variable]]
    file_path="/path/to/a/different/file.nc"
    var_name="elev"

You can include ```core.data.variable``` tags in different files. This can be useful to
group model-specific data with other model configuration options, and allow
configuration files to be swapped in a more modular fashion. However, the data
configurations across all files **must not** contain repeated data variable names.

.. code-block:: python

    # Load configured datasets
    data.load_data_config(config)

"""  # noqa: D205

from itertools import groupby
from pathlib import Path
from typing import Any

import numpy as np
from xarray import DataArray, Dataset

from virtual_ecosystem.core.axes import AXIS_VALIDATORS, validate_dataarray
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConfiguration
from virtual_ecosystem.core.readers import load_to_dataarray

# TODO: Model timing is currently used when writing the data to file to provide the
#       datestamps of the time_index dimension. This should probably be passed to
#       Data.__init__ so that it is available for all methods.


class Data:
    """The Virtual Ecosystem data object.

    This class holds data for a Virtual Ecosystem simulation. It functions like a
    dictionary but the class extends the dictionary methods to provide common methods
    for data validation etc and to hold key attributes, such as the underlying spatial
    grid.

    Args:
        grid: The Grid instance that will be used for simulation.

    Raises:
        TypeError: when grid is not a Grid object
    """

    def __init__(self, grid: Grid) -> None:
        # Set up the instance properties
        if not isinstance(grid, Grid):
            to_raise = TypeError("Data must be initialised with a Grid object")
            LOGGER.critical(to_raise)
            raise to_raise

        # Local import to avoid circular import issue
        from virtual_ecosystem.core.variables import (
            VariableMetadata,
            load_known_variables,
        )

        self.known_variables: dict[str, VariableMetadata] = load_known_variables()
        """A dictionary of known variables."""

        self.grid: Grid = grid
        """The configured Grid to be used in a simulation."""
        self.data = Dataset()
        """The :class:`~xarray.Dataset` used to store data."""
        self.variable_validation: dict[str, dict[str, str | None]] = {}
        """Records validation details for loaded variables.

        The validation details for each variable is stored in this dictionary using the
        variable name as a key. The validation details are a dictionary, keyed using
        core axis names, of the :class:`~virtual_ecosystem.core.axes.AxisValidator`
        subclass applied to that axis. If no validator was applied, the entry for that
        core axis will be ``None``.
        """

    def __repr__(self) -> str:
        """Returns a representation of a Data instance."""

        if self.data:
            return f"Data: {list(self.data.data_vars)}"

        return "Data: no variables loaded"

    def __setitem__(self, key: str, value: DataArray) -> None:
        """Load a data array into a Data instance.

        This method takes an input {class}`~xarray.DataArray` object and then matches
        the dimension and coordinates signature of the array to find a loading routine
        given the grid used in the {class}`virtual_ecosystem.core.data.Data` instance.
        That routine is used to validate the DataArray and then add the DataArray to the
        {class}`~xarray.Dataset` object or replace the existing DataArray under that
        key.

        Note that the DataArray name is expected to match the standard internal variable
        names used in Virtual Ecosystem and this is enforced against the dictionary of
        known variables.

        The method also adds unit and description metadata to from the known variables
        database to attributes as they are written to the data object.

        Args:
            key: The name to store the data under
            value: The DataArray to be stored

        Raises:
            TypeError: when the value is not a DataArray.
        """

        if not isinstance(value, DataArray):
            to_raise = TypeError(
                "Only DataArray objects can be added to Data instances"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        if key not in self.known_variables:
            msg = f"Attempt to add unknown variable to data: '{key}'"
            LOGGER.critical(msg)
            raise ValueError(msg)

        if key not in self.data.data_vars:
            LOGGER.info(f"Adding data array for '{key}'")
        else:
            LOGGER.info(f"Replacing data array for '{key}'")

        # Add variable_metadata from known variables database - these needs to be done
        # for both adding and replacing variables as the science models do not attempt
        # to persist array attributes during calculations.
        variable = self.known_variables[key]
        value.attrs.update({"unit": variable.unit, "description": variable.description})

        # Validate and store the data array
        value, valid_dict = validate_dataarray(value=value, grid=self.grid)
        self.data[key] = value
        self.variable_validation[key] = valid_dict

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
            ValueError: Either an unknown variable or core axis name or that the
                variable validation data in the Data instance does not include the
                variable, which would be an internal programming error.
        """

        if var_name not in self.data:
            raise ValueError(f"Unknown variable name: {var_name}")

        if var_name not in self.variable_validation:
            raise ValueError(f"Missing variable validation data: {var_name}")

        if axis_name not in AXIS_VALIDATORS:
            raise ValueError(f"Unknown core axis name: {axis_name}")

        if self.variable_validation[var_name][axis_name] is None:
            return False

        return True

    def load_data_config(self, config: CoreConfiguration) -> None:
        """Setup the simulation data from a user configuration.

        This is a method is used to validate a provided user data configuration and
        populate the Data instance object from the provided data sources. The
        data_config dictionary can contain a 'variable' key containing an array of
        dictionaries providing the path to the file (``file_path``) and the name of the
        variable within the file (``var_name``). The function groups variables by their
        source file path, so that each file is only opened once to load the requested
        variables.

        Args:
            config: A validated Virtual Ecosystem model configuration object.
        """

        LOGGER.info("Loading data from configuration")

        # Track errors in loading multiple files from a configuration
        data_config = config.data

        # The previous code here tested for "constant" and "generator" data types, but
        # since those are not yet implemented, this has been dropped

        # Handle variables
        if len(data_config.variable) == 0:
            LOGGER.warning("No data sources defined in the data configuration.")
            return

        clean_load = True

        # Check what name the data will be saved under but do then carry on to check
        # for other loading problems
        data_var_names = [var.var_name for var in data_config.variable]

        dupl_names = {str(md) for md in data_var_names if data_var_names.count(md) > 1}
        if dupl_names:
            LOGGER.error("Duplicate variable names in data configuration.")
            clean_load = False

        # Group variables by file
        variables = list(data_config.variable)
        variables.sort(key=lambda var: var.file_path)
        file_groups = groupby(variables, key=lambda var: var.file_path)

        # Load data from each data source
        for file, file_vars in file_groups:
            # Attempt to load the file, trapping exceptions as critical logger
            # messages and defer failure until the whole configuration has been
            # processed

            try:
                loaded_data = load_to_dataarray(
                    file=Path(file),
                    var_names=[var.var_name for var in file_vars],
                )

            except Exception as err:
                LOGGER.error(str(err))
                clean_load = False
            else:
                for var_name, data_array in loaded_data.items():
                    self[var_name] = data_array

        if not clean_load:
            msg = "Data configuration did not load cleanly - check log"
            LOGGER.critical(msg)
            raise ConfigurationError(msg)

    def save_to_zarr(
        self,
        output_file_path: Path,
        group: str | None = None,
        variables_to_save: list[str] | None = None,
    ) -> None:
        """Save variables from the data object to a Zarr store.

        Either the whole contents of the data object or specific variables of interest
        can be saved using this function.

        Args:
            output_file_path: Path location to save the Virtual Ecosystem model state.
            group: A zarr group to export the data to.
            variables_to_save: List of variables to be saved, defaulting to all
                variables.
        """

        # Check if all variables should be saved or just the requested ones.
        if variables_to_save:
            out = self.data[variables_to_save]
        else:
            out = self.data

        out.to_zarr(
            output_file_path, group=group, mode="a", consolidated=False, zarr_format=2
        )

    def save_current_state_to_zarr(
        self,
        output_file_path: Path,
        time_index: int,
        timestamp: np.datetime64,
        variables_to_save: list[str] = [],
        group: str | None = None,
    ) -> None:
        """Export requested variables in current data state to ``zarr`` format.

        Args:
            output_file_path: Path to the zarr data store.
            time_index: The time index of the slice being saved
            timestamp: The timestamp of the start of the timeslice
            variables_to_save: An optional list of variables to be exported.
            group: An optional zarr group to export the data to.
        """

        # Check if all variables should be saved or just the requested ones.
        if variables_to_save:
            out = self.data[variables_to_save]
        else:
            out = self.data

        # Create a dataset with the added time dimension and timestamp
        time_slice = out.expand_dims({"time_index": 1}).assign_coords(
            time_index=[time_index]
        )
        time_slice["timestamp"] = DataArray([timestamp], dims="time_index")

        # Save the variables to the zarr store, appending along time index after the
        # first time step. Zarr format 2 is used here because format 3 doesn't currently
        # handle fixed length strings, such as the PFT coords.
        #
        # TODO - will need to do something cleverer if we aren't writing all time steps
        #        and potentially skipping zero. Create a flag on data that records if
        #        any data has been written by this method
        if time_index == 0:
            time_slice.to_zarr(
                output_file_path,
                group=group,
                mode="a",
                consolidated=False,
                zarr_format=2,
            )
        else:
            time_slice.to_zarr(
                output_file_path,
                group=group,
                append_dim="time_index",
                consolidated=False,
                zarr_format=2,
            )

    def add_from_dict(self, output_dict: dict[str, DataArray]) -> None:
        """Update data object from dictionary of variables.

        This function takes a dictionary of updated variables to replace the
        corresponding variables in the data object. If a variable is not in data, it is
        added. This will need to be reassessed as the model evolves; TODO we might want
        to split the function in strict 'replace' and 'add' functionalities.

        Args:
            output_dict: dictionary of variables from submodule

        Returns:
            an updated data object for the current time step
        """

        for variable in output_dict:
            self[variable] = output_dict[variable]


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
        seed: int | None,
        method: str,  # one of the numpy.random.Generator methods
        **kwargs: Any,
    ) -> None:
        pass
