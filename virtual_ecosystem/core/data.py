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
(see :class:`~virtual_ecosystem.core.config.Config`). The expected
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

import dask
import numpy as np
from xarray import DataArray, Dataset, open_mfdataset

from virtual_ecosystem.core.axes import AXIS_VALIDATORS, validate_dataarray
from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.readers import load_to_dataarray
from virtual_ecosystem.core.utils import check_outfile

# There are ongoing xarray issues with NetCDF not being thread safe and this causes
# segfaults on different architectures in testing using `xarray.open_mfdataset`
# See:
# - https://github.com/pydata/xarray/issues/7079
# - https://github.com/pydata/xarray/issues/3961
#
# Following advice on both those issues, we currently explicitly stop dask from trying
# to use parallel file processing and use open_mfdataset(..., lock=False)
dask.config.set(scheduler="single-threaded")


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
        names used in Virtual Ecosystem.

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

        if key not in self.data.data_vars:
            LOGGER.info(f"Adding data array for '{key}'")
        else:
            LOGGER.info(f"Replacing data array for '{key}'")

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

    def load_data_config(self, config: Config) -> None:
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

        # Check the data configuration is provided - note that the default configuration
        # is to include cfg['core']['data'] = {} - so check first for something totally
        # broken/
        if ("core" not in config) or ("data" not in config["core"]):
            msg = "Data configuration not found in config object."
            LOGGER.critical(msg)
            raise ConfigurationError(msg)

        # Track errors in loading multiple files from a configuration
        data_config = config["core"]["data"]
        data_source_types = ["variable", "constant", "generator"]
        clean_load = True

        # Check for an empty data configuration - do not make this an error or critical
        # but do log it, so that users can trace back when variables are missing
        if not set(data_source_types).intersection(data_config):
            msg = "No data sources defined in the data configuration."
            LOGGER.warning(msg)

        # Handle variables
        if "variable" in data_config:
            # Check what name the data will be saved under but do then carry on to check
            # for other loading problems
            data_var_names = [v["var_name"] for v in data_config["variable"]]

            dupl_names = {
                str(md) for md in data_var_names if data_var_names.count(md) > 1
            }
            if dupl_names:
                LOGGER.error("Duplicate variable names in data configuration.")
                clean_load = False

            # Group variables by file
            variables = data_config["variable"]
            variables.sort(key=lambda v: v["file_path"])
            file_groups = groupby(variables, key=lambda v: v["file_path"])

            # Load data from each data source
            for file, file_vars in file_groups:
                # Attempt to load the file, trapping exceptions as critical logger
                # messages and defer failure until the whole configuration has been
                # processed

                try:
                    loaded_data = load_to_dataarray(
                        file=Path(file),
                        var_names=[var["var_name"] for var in file_vars],
                    )

                except Exception as err:
                    LOGGER.error(str(err))
                    clean_load = False
                else:
                    for var_name, data_array in loaded_data.items():
                        self[var_name] = data_array

        if "constant" in data_config:
            msg = "Data config for constants not yet implemented."
            LOGGER.critical(msg)
            raise NotImplementedError(msg)

        if "generator" in data_config:
            msg = "Data config for generators not yet implemented."
            LOGGER.critical(msg)
            raise NotImplementedError(msg)

        if not clean_load:
            msg = "Data configuration did not load cleanly - check log"
            LOGGER.critical(msg)
            raise ConfigurationError(msg)

    def save_to_netcdf(
        self, output_file_path: Path, variables_to_save: list[str] | None = None
    ) -> None:
        """Save the contents of the data object as a NetCDF file.

        Either the whole contents of the data object or specific variables of interest
        can be saved using this function.

        Args:
            output_file_path: Path location to save the Virtual Ecosystem model state.
            variables_to_save: List of variables to be saved. If not provided then all
                variables are saved.
        """

        # Check that the folder to save to exists and that there isn't already a file
        # saved there
        check_outfile(output_file_path)

        # If the file path is okay then write the model state out as a NetCDF. Should
        # check if all variables should be saved or just the requested ones.
        if variables_to_save:
            self.data[variables_to_save].to_netcdf(output_file_path)
        else:
            self.data.to_netcdf(output_file_path)

    def save_timeslice_to_netcdf(
        self, output_file_path: Path, variables_to_save: list[str], time_index: int
    ) -> None:
        """Save specific variables from current state of data as a NetCDF file.

        At present, this function save each time step individually. In future, this
        function might be altered to append multiple time steps at once, as this could
        improve performance significantly.

        Args:
            output_file_path: Path location to save NetCDF file to.
            variables_to_save: List of variables to save in the file
            time_index: The time index of the slice being saved

        Raises:
            ConfigurationError: If the file to save to can't be found
        """

        # Check that the folder to save to exists and that there isn't already a file
        # saved there
        check_outfile(output_file_path)

        # Loop over variables adding them to the new dataset
        time_slice = (
            self.data[variables_to_save]
            .expand_dims({"time_index": 1})
            .assign_coords(time_index=[time_index])
        )

        # Save and close new dataset
        time_slice.to_netcdf(Path(output_file_path))
        time_slice.close()

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

    def output_current_state(
        self,
        variables_to_save: list[str],
        data_options: dict[str, Any],
        time_index: int,
    ) -> Path:
        """Method to output the current state of the data object.

        This function outputs all variables stored in the data object, except for any
        data with a "time_index" dimension defined (at present only climate input data
        has this). This data can either be saved as a new file or appended to an
        existing file.

        Args:
            variables_to_save: List of variables to save
            data_options: Set of options concerning what to output and where
            time_index: The index representing the current time step in the data object.

        Raises:
            ConfigurationError: If the final output directory doesn't exist, isn't a
               directory, or the final output file already exists (when in new file
               mode). If the file to append to is missing (when not in new file mode).

        Returns:
            A path to the file that the current state is saved in
        """

        # Create output file path for specific time index
        out_path = (
            Path(data_options["out_folder_continuous"])
            / f"continuous_state{time_index:05}.nc"
        )

        # Save the required variables by appending to existing file
        self.save_timeslice_to_netcdf(out_path, variables_to_save, time_index)

        return out_path


def merge_continuous_data_files(
    data_options: dict[str, Any], continuous_data_files: list[Path]
) -> None:
    """Merge all continuous data files in a folder into a single file.

    This function deletes all of the continuous output files it has been asked to merge
    once the combined output is saved.

    Args:
        data_options: Set of options concerning what to output and where
        continuous_data_files: Files containing previously output continuous data

    Raises:
        ConfigurationError: If output folder doesn't exist or if it output file already
            exists
    """

    # Path to folder containing the continuous output (that merged file should be saved
    # to)
    out_path = (
        Path(data_options["out_folder_continuous"])
        / data_options["out_continuous_file_name"]
    )

    # Check that output file doesn't already exist
    check_outfile(out_path)

    # Open all files as a single dataset
    with open_mfdataset(continuous_data_files, lock=False) as all_data:
        # Specify type of the layer roles object to allow for quicker saving by dask
        all_data["layer_roles"] = all_data["layer_roles"].astype("S9")

        # Save and close complete dataset
        all_data.to_netcdf(out_path)

    # Iterate over all continuous files and delete them
    for file_path in continuous_data_files:
        file_path.unlink()


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
