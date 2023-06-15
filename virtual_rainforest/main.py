"""The :mod:`~virtual_rainforest.main` module defines the function used to run a full
simulation of the model, along with helper functions to validate and configure the
model.
"""  # noqa: D205, D415

from math import ceil
from pathlib import Path
from typing import Any, Type, Union

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import MODEL_REGISTRY, BaseModel
from virtual_rainforest.core.config import Config
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER


def select_models(model_list: list[str]) -> list[Type[BaseModel]]:
    """Select the models to be run for a specific virtual rainforest simulation.

    This function looks for models from a list of models, if these models can all be
    found in the registry then they are returned. Otherwise an error is logged, which
    should be handled appropriately downstream.

    Args:
        model_list: A list of models to select

    Raises:
        InitialisationError: If one or more models cannot be found in the registry
    """

    # Remove "core" from model list as it is not a model
    model_list_ = set(model_list) - {"core"}

    LOGGER.info(
        "Attempting to configure the following models: %s" % sorted(model_list_)
    )

    # Make list of missing models, and return an error if necessary
    miss_model = [model for model in model_list_ if model not in MODEL_REGISTRY.keys()]
    if miss_model:
        to_raise = InitialisationError(
            f"The following models cannot be configured as they are not found in the "
            f"registry: {miss_model}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # Then extract each model from the registry
    modules = [MODEL_REGISTRY[model] for model in model_list_]

    return modules


def configure_models(
    config: dict[str, Any],
    data: Data,
    model_list: list[Type[BaseModel]],
    update_interval: pint.Quantity,
) -> dict[str, BaseModel]:
    """Configure a set of models for use in a `virtual_rainforest` simulation.

    Args:
        config: The full virtual rainforest configuration
        data: A Data instance.
        modules: A set of models to be configured
        update_interval: The interval with which each model is updated

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = {}
    for model in model_list:
        try:
            this_model = model.from_config(data, config, update_interval)
            models_cfd[this_model.model_name] = this_model
        except (InitialisationError, ConfigurationError):
            failed_models.append(model.model_name)

    # If any models fail to configure inform the user about it
    if failed_models:
        to_raise = InitialisationError(
            f"Could not configure all the desired models, ending the simulation. The "
            f"following models failed: {failed_models}."
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return models_cfd


def extract_timing_details(
    config: dict[str, Any]
) -> tuple[datetime64, timedelta64, pint.Quantity, datetime64]:
    """Extract timing details for main loop from the model configuration.

    The start time, run length and update interval are all extracted from the
    configuration. Sanity checks are carried out on these extracted values. The end time
    is then generated from the previously extracted timing information. This end time
    will always be a multiple of the update interval, with the convention that the
    simulation should always run for at least as long as the user specified run
    length.

    Args:
        config: The full virtual rainforest configuration

    Raises:
        InitialisationError: If the run length is too short for the model to update, or
            the units of update interval or run length aren't valid.
    """

    # First extract start and end times
    start_time = datetime64(config["core"]["timing"]["start_date"])

    # Catch bad time dimensions
    try:
        raw_length = pint.Quantity(config["core"]["timing"]["run_length"]).to("seconds")
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        to_raise = InitialisationError(
            "Units for core.timing.run_length are not valid time units: %s"
            % config["core"]["timing"]["run_length"]
        )
        LOGGER.critical(to_raise)
        raise to_raise
    else:
        # Round raw time interval to nearest second
        run_length = timedelta64(round(raw_length.magnitude), "s")

    # Catch bad time dimensions
    try:
        # This averages across months and years (i.e. 1 month => 30.4375 days)
        raw_interval = pint.Quantity(config["core"]["timing"]["update_interval"]).to(
            "seconds"
        )
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        to_raise = InitialisationError(
            "Units for core.timing.update_interval are not valid time units: %s"
            % config["core"]["timing"]["update_interval"]
        )
        LOGGER.critical(to_raise)
        raise to_raise
    else:
        # Round raw time interval to nearest second
        update_interval = timedelta64(round(raw_interval.magnitude), "s")

    if run_length < update_interval:
        to_raise = InitialisationError(
            f"Models will never update as the update interval ({update_interval}) is "
            f"larger than the run length ({run_length})"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # Calculate when the simulation should stop based on principle that it should run at
    # least as long as the user requests rather than shorter
    end_time = start_time + ceil(run_length / update_interval) * update_interval

    # Then inform the user how long it will run for
    LOGGER.info(
        "Virtual Rainforest simulation will run from %s until %s. This is a run length "
        "of %s, the user requested %s"
        % (start_time, end_time, end_time - start_time, run_length)
    )

    return start_time, update_interval, raw_interval, end_time


def output_current_state(
    data: Data,
    models_cfd: dict[str, BaseModel],
    data_options: dict[str, Any],
    new_file: bool = False,
) -> None:
    """Function to output the current state of the data object.

    This function outputs all variables stored in the data object, except for any data
    with a "time_index" dimension defined (at present only climate input data has this).
    This data can either be saved as a new file or appended to an existing file.

    Args:
        data: Data object to output current state of
        models_cfd: Set of models configured for use in the simulation
        data_options: Set of options concerning what to output and where
        new_file: Whether or not to generate a new file, rather than appending to an
            existing one

    Raises:
        ConfigurationError: If the final output directory doesn't exist, isn't a
           directory, or the final output file already exists (when in new file mode).
           If the file to append to is missing (when not in new file mode).
    """

    # Only variables in the data object that are updated by a model should be outputted
    all_variables = [
        models_cfd[model_nm].vars_updated for model_nm in models_cfd.keys()
    ]
    # Then flatten the list
    variables_to_save = [item for sublist in all_variables for item in sublist]
    # TODO - Find time_index so that it can be used to create the file name
    # TODO - Work out how to sensibly create the file name

    # First decide whether to generate a new file or append to an existing one
    if new_file:
        # Save the required variables (as a new file)
        data.save_to_netcdf(
            Path(data_options["out_path_continuous"]), variables_to_save
        )
    else:
        # TODO - Append function should become save_with_index or similar, as it no
        # longer appends but it is different from the other
        # Save the required variables by appending to existing file
        data.append_to_netcdf(
            Path(data_options["out_path_continuous"]), variables_to_save
        )


def vr_run(
    cfg_paths: Union[str, Path, list[Union[str, Path]]], merge_file_path: Path
) -> None:
    """Perform a virtual rainforest simulation.

    This is a high-level function that runs a virtual rainforest simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        merge_file_path: Path to save merged config file to (i.e. folder location + file
            name)
    """

    config = Config(cfg_paths)
    config.export_config(merge_file_path)

    grid = Grid.from_config(config)
    data = Data(grid)
    data.load_data_config(config["core"]["data"])

    model_list = select_models(config["core"]["modules"])

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    # Extract all the relevant timing details
    (
        current_time,
        update_interval,
        update_interval_as_quantity,
        end_time,
    ) = extract_timing_details(config)

    models_cfd = configure_models(config, data, model_list, update_interval_as_quantity)

    LOGGER.info(
        "All models successfully configured, now attempting to initialise them."
    )

    # Setup all models (those with placeholder setup processes won't change at all)
    for mod_nm in models_cfd:
        models_cfd[mod_nm].setup()

    LOGGER.info("All models successfully set up, now attempting to run them.")

    # TODO - A model spin up might be needed here in future

    # Save the initial state of the model
    if config["core"]["data_output_options"]["save_initial_state"]:
        data.save_to_netcdf(
            Path(config["core"]["data_output_options"]["out_path_initial"])
        )

    # Make file and save time = 0 data to it. This is different to the initial state as
    # it only contains variables we update with time (i.e. not the input climate data)
    if config["core"]["data_output_options"]["save_continuous_data"]:
        output_current_state(
            data, models_cfd, config["core"]["data_output_options"], new_file=True
        )

    # Setup the timing loop
    time_index = 0
    while current_time < end_time:
        current_time += update_interval

        # Run update() method for every model
        for mod_nm in models_cfd:
            models_cfd[mod_nm].update(time_index)

        # With updates complete increment the time_index
        time_index += 1

        # Append updated data to the continuous data file
        if config["core"]["data_output_options"]["save_continuous_data"]:
            output_current_state(
                data, models_cfd, config["core"]["data_output_options"]
            )

    # Save the final model state
    if config["core"]["data_output_options"]["save_final_state"]:
        data.save_to_netcdf(
            Path(config["core"]["data_output_options"]["out_path_final"])
        )

    LOGGER.info("Virtual rainforest model run completed!")
