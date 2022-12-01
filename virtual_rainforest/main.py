"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

from itertools import compress
from math import ceil
from pathlib import Path
from typing import Any, Type, Union

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.model import MODEL_REGISTRY, BaseModel, InitialisationError


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
        log_and_raise(
            f"The following models cannot be configured as they are not found in the "
            f"registry: {miss_model}",
            InitialisationError,
        )

    # Then extract each model from the registry
    modules = [MODEL_REGISTRY[model] for model in model_list_]

    return modules


def configure_models(
    config: dict[str, Any], model_list: list[Type[BaseModel]]
) -> list[BaseModel]:
    """Configure a set of models for use in a `virtual_rainforest` simulation.

    Args:
        config: The full virtual rainforest configuration
        modules: A set of models to be configured

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = []
    for model in model_list:
        try:
            models_cfd.append(model.from_config(config))
        except InitialisationError:
            failed_models.append(model.name)

    # If any models fail to configure inform the user about it
    if failed_models:
        log_and_raise(
            f"Could not configure all the desired models, ending the simulation. The "
            f"following models failed: {failed_models}.",
            InitialisationError,
        )

    return models_cfd


def extract_timing_details(
    config: dict[str, Any]
) -> tuple[datetime64, datetime64, timedelta64, datetime64]:
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
        raw_length = pint.Quantity(config["core"]["timing"]["run_length"]).to("minutes")
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        log_and_raise(
            "Units for core.timing.run_length are not valid time units: %s"
            % config["core"]["timing"]["run_length"],
            InitialisationError,
        )
    else:
        # Round raw time interval to nearest minute
        run_length = timedelta64(int(raw_length.magnitude), "m")

    # Catch bad time dimensions
    try:
        raw_interval = pint.Quantity(config["core"]["timing"]["main_time_step"]).to(
            "minutes"
        )
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        log_and_raise(
            "Units for core.timing.main_time_step are not valid time units: %s"
            % config["core"]["timing"]["main_time_step"],
            InitialisationError,
        )
    else:
        # Round raw time interval to nearest minute
        update_interval = timedelta64(int(raw_interval.magnitude), "m")

    if run_length < update_interval:
        log_and_raise(
            f"Models will never update as the update interval ({update_interval}) is "
            f"larger than the run length ({run_length})",
            InitialisationError,
        )

    # Calculate when the simulation should stop based on principle that it should run at
    # least as long as the user requests rather than shorter
    end_time = start_time + ceil(run_length / update_interval) * update_interval

    # Then inform the user how long it will run for
    LOGGER.info(
        "Virtual Rainforest simulation will run from %s until %s. This is a run length "
        "of %s, the user requested %s"
        % (start_time, end_time, end_time - start_time, run_length)
    )

    # TODO - WORK OUT WHICH OF THESE SHOULD ACTUALLY BE RETURNED
    return start_time, end_time, update_interval, start_time


def check_for_fast_models(
    models_cfd: list[BaseModel], update_interval: timedelta64
) -> None:
    """Warn user of any models using a faster time step than update interval.

    Args:
        models_cfd: Set of initialised models
        update_interval: Time step of the main model loop
    """
    fast_models = [
        model.name for model in models_cfd if model.update_interval < update_interval
    ]
    if fast_models:
        LOGGER.warning(
            "The following models have shorter time steps than the main model: %s"
            % fast_models
        )


def get_models_to_update(
    current_time: datetime64, models: list[BaseModel]
) -> tuple[list[BaseModel], list[BaseModel]]:
    """Split set of models based on whether they should be updated.

    Args:
        current_time: Main timing loop time step
        models: Full set of models
    """

    # Find models to update
    to_update = [model.should_update(current_time) for model in models]

    # Separate models into lists based on whether they should update or not
    to_refresh = list(compress([mod for mod in models], to_update))
    fixed = list(compress([mod for mod in models], [not elem for elem in to_update]))

    return (to_refresh, fixed)


def vr_run(
    cfg_paths: Union[str, list[str]],
    merge_file_path: Path,
) -> None:
    """Perform a virtual rainforest simulation.

    This is a high-level function that runs a virtual rainforest simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        merge_file_path: Path to save merged config file to
    """

    config = validate_config(cfg_paths, merge_file_path)

    model_list = select_models(config["core"]["modules"])

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    models_cfd = configure_models(config, model_list)

    LOGGER.info(
        "All models successfully configured, now attempting to initialise them."
    )

    # Extract all the relevant timing details
    start_time, end_time, update_interval, current_time = extract_timing_details(config)

    # Identify models with shorter time steps than main loop and warn user about them
    check_for_fast_models(models_cfd, update_interval)

    # TODO - Extract input data required to initialise the models

    # TODO - Initialise the set of configured models

    # TODO - Spin up the models

    # Start timing for all models
    for model in models_cfd:
        model.start_model_timing(start_time)

    # TODO - Save model state

    # Setup the timing loop
    while current_time < end_time:

        current_time += update_interval

        to_refresh, fixed = get_models_to_update(current_time, models_cfd)

        # TODO - Solve models to steady state

        models_cfd = to_refresh + fixed

        # TODO - Save model state

    LOGGER.info("Virtual rainforest model run completed!")
