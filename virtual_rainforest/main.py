"""The :mod:`~virtual_rainforest.main` module defines the function used to run a full
simulation of the model, along with helper functions to validate and configure the
model.
"""  # noqa: D205, D415

import os
from collections.abc import Sequence
from graphlib import CycleError, TopologicalSorter
from itertools import chain
from math import ceil
from pathlib import Path
from typing import Any, Optional, Union

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.config import Config
from virtual_rainforest.core.data import Data, merge_continuous_data_files
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER, add_file_logger, remove_file_logger


def initialise_models(
    config: Config,
    data: Data,
    models: dict[str, Any],  # FIXME -> dict[str, Type[BaseModel]]
    update_interval: pint.Quantity,
) -> dict[str, Any]:  # FIXME -> dict[str, Type[BaseModel]]
    """Initialise a set of models for use in a `virtual_rainforest` simulation.

    Args:
        config: A validated Virtual Rainforest model configuration object.
        data: A Data instance.
        modules: A dictionary of models to be configured.
        update_interval: The interval with which each model is updated

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    LOGGER.info("Initialising models: %s" % ",".join(models.keys()))

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = {}
    for model_name, model_class in models.items():
        try:
            this_model = model_class.from_config(data, config, update_interval)
            models_cfd[model_name] = this_model
        except (InitialisationError, ConfigurationError):
            failed_models.append(model_name)

    # If any models fail to configure inform the user about it
    if failed_models:
        to_raise = InitialisationError(
            f"Configuration failed for models: {','.join(failed_models)}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return models_cfd


def extract_timing_details(
    config: Config,
) -> tuple[datetime64, timedelta64, pint.Quantity, datetime64]:
    """Extract timing details for main loop from the model configuration.

    The start time, run length and update interval are all extracted from the
    configuration. Sanity checks are carried out on these extracted values. The end time
    is then generated from the previously extracted timing information. This end time
    will always be a multiple of the update interval, with the convention that the
    simulation should always run for at least as long as the user specified run
    length.

    Args:
        config: A validated Virtual Rainforest model configuration object.

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


def _get_model_sequence(
    config: Config, models: dict[str, Any], method: str
) -> dict[str, Any]:  # FIXME dict[str, Any]-> dict[str, Type[BaseModel]]
    """Get a tuple of the model execution sequence for a given model stage.

    This function uses the ``priority`` sections in model configurations to establish an
    execution sequence for a given model method (currently, one of ``init`` or
    ``update``). For example, the configuration:

    .. code-block:: toml
        [plants.priorities]
        init = ['abiotic']
        update = ['abiotic']

    would set that the ``plants`` model should be both initialised and updated before
    the ``abiotic`` model.

    Args:
        config: A validated configuration object.
        models: A dictionary of model subclasses or instances.
        method: The :class:`~virtual_rainforest.core.base_model.BaseModel` method to use
            to define the model execution sequence.

    Returns:
        The function returns a dictionary, keyed by model name, of model classes or
        instances in the requested execution order.

    Raises:
        ConfigurationError: if the configuration priority details include a model name
            that is not included in the configuration or if the configuration priorities
            are cyclic.
    """

    # Extract priority information for the models for the given step
    priorities: dict[str, list[str]] = {}
    for model_name in models:
        priorities[model_name] = config[model_name]["priority"][method]

    # Find a resolved running order for those priorities
    sorter = TopologicalSorter(priorities)

    # Find a resolved execution order, checking for cyclic priorities
    try:
        resolved_order: tuple[str, ...] = tuple(sorter.static_order())
    except CycleError as excep:
        to_raise = f"Model {method} priorities are cyclic: {', '.join(excep.args[1])}"
        LOGGER.critical(to_raise)
        raise ConfigurationError(to_raise)

    # Return a dictionary of models in execution order
    return {model_name: models[model_name] for model_name in (reversed(resolved_order))}


def vr_run(
    cfg_paths: Union[str, Path, Sequence[Union[str, Path]]] = [],
    cfg_strings: Union[str, list[str]] = [],
    override_params: dict[str, Any] = {},
    logfile: Optional[Path] = None,
) -> None:
    """Perform a virtual rainforest simulation.

    This is a high-level function that runs a virtual rainforest simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        cfg_strings: An alternate string providing TOML formatted configuration data
        override_params: Extra parameters provided by the user
        logfile: An optional path to a log file, otherwise logging will print to the
            console.
    """

    # Switch from console logging to file logging
    if logfile is not None:
        add_file_logger(logfile)

    config = Config(
        cfg_paths=cfg_paths, cfg_strings=cfg_strings, override_params=override_params
    )

    # Save the merged config if requested
    data_opt = config["core"]["data_output_options"]
    if data_opt["save_merged_config"]:
        outfile = Path(data_opt["out_path"]) / data_opt["out_merge_file_name"]
        config.export_config(outfile)

    # Build core elements
    grid = Grid.from_config(config)
    data = Data(grid)
    data.load_data_config(config)

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    # Extract all the relevant timing details
    (
        current_time,
        update_interval,
        update_interval_as_quantity,
        end_time,
    ) = extract_timing_details(config)

    # Get the model initialisation sequence and initialise
    init_sequence = _get_model_sequence(
        config=config, models=config.model_classes, method="init"
    )
    models_init = initialise_models(
        config=config,
        data=data,
        models=init_sequence,
        update_interval=update_interval_as_quantity,
    )

    LOGGER.info("All models successfully intialised.")

    # Setup all models (those with placeholder setup processes won't change at all)
    for model in models_init.values():
        model.setup()

    LOGGER.info("All models successfully set up.")

    # TODO - A model spin up might be needed here in future

    # Create output folder if it does not exist
    out_path = Path(config["core"]["data_output_options"]["out_path"])
    os.makedirs(out_path, exist_ok=True)

    # Save the initial state of the model
    if config["core"]["data_output_options"]["save_initial_state"]:
        data.save_to_netcdf(
            out_path / config["core"]["data_output_options"]["out_initial_file_name"]
        )

    # If no path for saving continuous data is specified, fall back on using out_path
    if "out_folder_continuous" not in config["core"]["data_output_options"]:
        config["core"]["data_output_options"]["out_folder_continuous"] = str(out_path)

    # Container to store paths to continuous data files
    continuous_data_files = []

    # Only variables in the data object that are updated by a model should be output
    all_variables = (model.vars_updated for model in models_init.values())
    # Then flatten the list to generate list of variables to output
    variables_to_save = list(chain.from_iterable(all_variables))

    # Take the models in their current execution sequence and change to the model update
    # sequence
    models_update = _get_model_sequence(
        config=config, models=models_init, method="update"
    )

    # Setup the timing loop
    time_index = 0
    while current_time < end_time:
        current_time += update_interval

        # Run update() method for every model
        for model in models_update.values():
            model.update(time_index)

        # With updates complete increment the time_index
        time_index += 1

        # Append updated data to the continuous data file
        if config["core"]["data_output_options"]["save_continuous_data"]:
            outfile_path = data.output_current_state(
                variables_to_save, config["core"]["data_output_options"], time_index
            )
            continuous_data_files.append(outfile_path)

    # Merge all files together based on a list
    if config["core"]["data_output_options"]["save_continuous_data"]:
        merge_continuous_data_files(
            config["core"]["data_output_options"], continuous_data_files
        )

    # Save the final model state
    if config["core"]["data_output_options"]["save_final_state"]:
        data.save_to_netcdf(
            out_path / config["core"]["data_output_options"]["out_final_file_name"]
        )

    LOGGER.info("Virtual rainforest model run completed!")

    # Restore default logging settings
    if logfile is not None:
        remove_file_logger()
