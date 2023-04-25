"""The :mod:`~virtual_rainforest.main` module defines the function used to run a full
simulation of the model, along with helper functions to validate and configure the
model.
"""  # noqa: D205, D415

# TODO - Update documentation of main simulation flow to reflect changes

from math import ceil
from pathlib import Path
from typing import Any, Type, Union

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import MODEL_REGISTRY, BaseModel
from virtual_rainforest.core.config import validate_config
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


# TODO - Think I need extra testing here
def configure_models(
    config: dict[str, Any], data: Data, model_list: list[Type[BaseModel]]
) -> dict[str, BaseModel]:
    """Configure a set of models for use in a `virtual_rainforest` simulation.

    Args:
        config: The full virtual rainforest configuration
        data: A Data instance.
        modules: A set of models to be configured

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = {}
    for model in model_list:
        try:
            this_model = model.from_config(data, config)
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
) -> tuple[datetime64, timedelta64, datetime64]:
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
        # TODO - Document what this unit transformation does (i.e. month = 30.4375 days)
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
        update_interval = timedelta64(int(round(raw_interval.magnitude)), "s")

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

    return start_time, update_interval, end_time


# TODO - Work out if any more tested is needed for this main flow
def vr_run(cfg_paths: Union[str, list[str]], merge_file_path: Path) -> None:
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

    config = validate_config(cfg_paths, merge_file_path)

    grid = Grid()  # TODO - this needs a Grid.from_config factory function
    data = Data(grid)
    data.load_data_config(config["core"]["data"])

    model_list = select_models(config["core"]["modules"])

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    models_cfd = configure_models(config, data, model_list)

    LOGGER.info(
        "All models successfully configured, now attempting to initialise them."
    )

    # Extract all the relevant timing details
    current_time, update_interval, end_time = extract_timing_details(config)

    # TODO - A model spin up might be needed here in future

    # Save the initial state of the model
    if config["core"]["data_output_options"]["save_initial_state"]:
        data.save_to_netcdf(
            Path(config["core"]["data_output_options"]["out_path_initial"])
        )

    # Setup the timing loop
    while current_time < end_time:
        current_time += update_interval

        # Run update() method for every model
        for mod_nm in models_cfd:
            models_cfd[mod_nm].update()

    # Save the final model state
    if config["core"]["data_output_options"]["save_final_state"]:
        data.save_to_netcdf(
            Path(config["core"]["data_output_options"]["out_path_final"])
        )

    LOGGER.info("Virtual rainforest model run completed!")
