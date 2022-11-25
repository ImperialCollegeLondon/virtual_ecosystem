"""Defines the function used to run a full simulation of the model.

As well as setting up the function to run the overall virtual rainforest simulation,
this script also defines the command line entry points for the model.
"""

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
) -> tuple[datetime64, datetime64, timedelta64]:
    """Extract timing details for main loop from the model configuration.

    Args:
        config: The full virtual rainforest configuration

    Raises:
        InitialisationError: If the model is set to end before it starts, the units of
            update interval aren't valid, or if the interval is too small for the model
            to ever update.
    """

    # First extract start and end times
    start_time = datetime64(config["core"]["timing"]["start_date"])
    end_time = datetime64(config["core"]["timing"]["end_date"])

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

    if end_time < start_time:
        log_and_raise(
            f"Simulation ends ({start_time}) before it starts ({end_time})!",
            InitialisationError,
        )

    if update_interval > end_time - start_time:
        log_and_raise(
            f"Model will never update as update interval ({update_interval}) is larger "
            f"than the difference between the start and end times "
            f"({end_time - start_time})",
            InitialisationError,
        )

    return start_time, end_time, update_interval


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


def setup_timing_loop(
    start_time: datetime64, end_time: datetime64, update_interval: timedelta64
) -> datetime64:
    """Setup timing loop by returning the current time.

    Also check if the time interval chosen means that more than 10% of the time window
    is not covered. If this is the case the user is warned.

    Args:
        start_time: Time the model starts at
        end_time: Time the model should end at
        update_interval: Time step of the main model loop
    """

    # Print number of steps needed to cover the interval
    n = (end_time - start_time) / update_interval
    # Convert this to a percentage of time span not covered
    _, d = divmod(n, 1)
    p = 100 * d / n

    if p > 5.0:
        LOGGER.warning(
            "Due to a (relatively) large model time step, %.4s%% of the desired time "
            "span is not covered!" % p
        )

    return start_time


def vr_run(
    cfg_paths: Union[str, list[str]], output_folder: str, out_file_name: str
) -> None:
    """Perform a virtual rainforest simulation.

    This is a high-level function that runs a virtual rainforest simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        output_folder: Folder to save combined configuration to
        out_file_name: Name for the combined configuration file
    """

    config = validate_config(cfg_paths, output_folder, out_file_name)

    model_list = select_models(config["core"]["modules"])

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    models_cfd = configure_models(config, model_list)

    LOGGER.info(
        "All models successfully configured, now attempting to initialise them."
    )

    # Extract all the relevant timing details
    start_time, end_time, update_interval = extract_timing_details(config)

    # Identify models with shorter time steps than main loop and warn user about them
    check_for_fast_models(models_cfd, update_interval)

    # TODO - Extract input data required to initialise the models

    # TODO - Initialise the set of configured models

    # TODO - Spin up the models

    # Start timing for all models
    for model in models_cfd:
        model.start_model_timing(start_time)

    # TODO - Save model state

    # TODO - Add timing loop
    current_time = setup_timing_loop(start_time, end_time, update_interval)
    while current_time < end_time:

        # TODO - ACTUALLY DO SOMETHING HERE
        current_time += update_interval

    # TODO - Find models to update
    # TODO - Solve models to steady state
    # TODO - Save model state

    LOGGER.info("Virtual rainforest model run completed!")


# TODO - Define command line entry point
