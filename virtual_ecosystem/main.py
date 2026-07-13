"""The :mod:`~virtual_ecosystem.main` module defines the function used to run a full
simulation of the model, along with helper functions to validate and configure the
model.
"""  # noqa: D205

import sys
from collections.abc import Sequence
from enum import IntEnum
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

from tqdm import tqdm

from virtual_ecosystem.core.base_model import BaseDisturbance, BaseModel
from virtual_ecosystem.core.config_builder import (
    ConfigurationLoader,
    generate_configuration,
)
from virtual_ecosystem.core.configuration import (
    CompiledConfiguration,
    DisturbanceConfigurationRoot,
)
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.core.logger import LOGGER, add_file_logger, remove_file_logger
from virtual_ecosystem.core.model_config import (
    CoreConfiguration,
)
from virtual_ecosystem.core.variables import (
    get_model_order,
    setup_variables,
)


class Progress(IntEnum):
    """Integer enumeration to manage ve_run output verbosity."""

    SILENT = 0
    MINIMAL = 1
    STAGED = 2
    FULL = 3


def check_added_variables(
    before: list[str], after: list[str], claimed: tuple[str, ...], model: str, attr: str
) -> None:
    """Check the variables added to data during a model step.

    This function checks that the difference in the set of variable names added to data
    during a model step match the set of variables that the model `var_` attributes
    claims for the model.

    Args:
        before: A list of data variable names from before the model method ran.
        after: A list of data variable names from after the model method ran.
        claimed: The model attribute describing the claimed set of variables added.
        model: The name of the model being checked
        attr: The variable attribute name being checked

    Raises:
        InitialisationError: if the actual changed variables do matched the variables
            configured in the model attributes.
    """

    actual_set = set(after) - set(before)
    claimed_set = set(claimed)

    # If the update variables agree with the model definition then return
    if actual_set == claimed_set:
        return

    # Otherwise log the mismatch and raise an error.
    LOGGER.critical(
        f"Mismatch between {model}.{attr} and variable changes in the data:"
    )

    claimed_not_actual = claimed_set - actual_set
    if claimed_not_actual:
        LOGGER.critical(f"Claimed but not populated: {','.join(claimed_not_actual)}")

    actual_not_claimed = actual_set - claimed_set
    if actual_not_claimed:
        LOGGER.critical(f"Populated but not claimed: {','.join(actual_not_claimed)}")

    raise InitialisationError(f"Variable setup errors in {model} model: check log.")


def initialise_models(
    configuration: CompiledConfiguration,
    data: Data,
    core_components: CoreComponents,
    models: dict[str, type[BaseModel]],
) -> dict[str, BaseModel]:
    """Initialise a set of models for use in a `virtual_ecosystem` simulation.

    Args:
        configuration: A validated Virtual Ecosystem model configuration object.
        config: A validated Virtual Ecosystem model configuration object.
        data: A Data instance.
        core_components: A CoreComponents instance.
        models: A dictionary of models to be configured.

    Raises:
        InitialisationError: If one or more models cannot be properly configured
    """

    LOGGER.info("Initialising models: {}".format(",".join(models.keys())))

    # Use factory methods to configure the desired models
    failed_models = []
    models_cfd = {}

    for model_name, model_class in models.items():
        LOGGER.info(f"Initialising {model_name} model")

        try:
            data_vars_before_init = [str(i) for i in data.data.data_vars]
            this_model = model_class.from_config(
                data=data,
                configuration=configuration,
                core_components=core_components,
            )
            models_cfd[model_name] = this_model
            data_vars_after_init = [str(i) for i in data.data.data_vars]

            # If there are mismatches in the variable specifications, fail.
            check_added_variables(
                before=data_vars_before_init,
                after=data_vars_after_init,
                claimed=model_class.vars_populated_by_init,
                model=model_name,
                attr="vars_populated_by_init",
            )

        except (InitialisationError, ConfigurationError):
            failed_models.append(model_name)

    # If any models fail to configure inform the user about it
    if failed_models:
        to_raise: Exception = InitialisationError(
            f"Configuration failed for models: {','.join(failed_models)}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return models_cfd


def sort_disturbances(configuration: CompiledConfiguration) -> list[str]:
    """Sort disturbances based on priority and name.

    Args:
        configuration: CompiledConfiguration object for disturbances.

    Returns:
        Tuple of disturbance model names in the order they need to be executed.
    """
    disturbance_config = configuration.get_disturbance_config()
    if not disturbance_config:
        return []

    priorities = {
        name: -disturbance_config.get_subconfiguration(
            name, DisturbanceConfigurationRoot
        ).priority
        for name in disturbance_config._model_classes.keys()
    }
    if len(set(priorities.values())) != len(priorities):
        to_raise: Exception = InitialisationError(
            "Configuration failed for disturbances: 2 or more disturbance models have "
            "the same priority"
        )
        LOGGER.critical(to_raise)
    return sorted(priorities.keys(), key=lambda name: priorities[name])


def initialise_disturbances(
    configuration: CompiledConfiguration,
    data: Data,
    core_components: CoreComponents,
    models: dict[str, BaseModel],
) -> dict[str, BaseDisturbance]:
    """Initialise a set of disturbances for use in a `virtual_ecosystem` simulation.

    Args:
        configuration: A validated Virtual Ecosystem configuration object containing the
            disturbance configuration.
        data: A Data instance.
        core_components: A CoreComponents instance.
        models: A dictionary of initialised models.

    Raises:
        InitialisationError: If one or more disturbances cannot be properly configured

    Returns:
        Dictionary of initialised disturbances in the right execution order.
    """
    sorted_disturbances = sort_disturbances(configuration)

    LOGGER.info("Initialising disturbances: {}".format(",".join(sorted_disturbances)))

    # Use factory methods to configure the desired disturbances
    failed_disturbances = []
    models_cfd = {}

    # We do know there are disturbances at this point, so this casting is OK.
    disturbance_config = cast(
        CompiledConfiguration, configuration.get_disturbance_config()
    )

    for disturbance_name in sorted_disturbances:
        LOGGER.info(f"Initialising {disturbance_name} disturbance")

        try:
            disturbance_class: BaseDisturbance = disturbance_config._model_classes[
                disturbance_name
            ]
            this_disturbance = disturbance_class.from_config(
                data=data,
                configuration=configuration,
                core_components=core_components,
                models=models,
            )
            models_cfd[disturbance_name] = this_disturbance

        except (InitialisationError, ConfigurationError, KeyError):
            failed_disturbances.append(disturbance_name)

    # If any models fail to configure inform the user about it
    if failed_disturbances:
        to_raise: Exception = InitialisationError(
            f"Configuration failed for disturbances: {','.join(failed_disturbances)}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return models_cfd


def ve_run(
    cfg_paths: str | Path | Sequence[str | Path] = [],
    cfg_strings: str | list[str] = [],
    cli_config: dict[str, Any] = {},
    cli_paths: dict[str, Path] = {},
    logfile: Path | None = None,
    validate_only: bool = False,
    progress: Progress = Progress.FULL,
) -> None:
    """Perform a Virtual Ecosystem simulation.

    This is a high-level function that runs a Virtual Ecosystem simulation. At the
    moment this involves validating an input configuration, and using this configuration
    to generate a set of configured model objects suitable for downstream use. Down the
    line this should be extended to encompass far more steps.

    Args:
        cfg_paths: Set of paths to configuration files
        cfg_strings: An alternate string providing TOML formatted configuration data
        cli_config: Configuration settings provided by the user at the command line,
            used to override configuration settings in files.
        cli_paths: Configuration settings provided by the user at the command line,
            used to dynamically set paths to input data files.
        logfile: An optional path to a log file, otherwise logging will print to the
            console.
        validate_only: Should the command exit after config validation.
        progress: A Progress enum instance setting the level of output to be printed to
            the console when ve_run is running.
    """

    # Mute the progress information when the log is written to stdout.
    if logfile is None:
        progress = Progress.SILENT

    if progress > Progress.SILENT:
        print(
            "* Starting Virtual Ecosystem simulation using v"
            f"{version('virtual_ecosystem')}."
        )

    # Switch from console logging to file logging
    if logfile is not None:
        add_file_logger(logfile)
        LOGGER.info(f"Using Virtual Ecosystem v{version('virtual_ecosystem')}.")
        if progress > Progress.SILENT:
            print(f"* Logging to: {logfile}")

    if progress > Progress.MINIMAL:
        print("* Loading configuration")

    # Load the configuration data
    config_data: ConfigurationLoader = ConfigurationLoader(
        cfg_paths=cfg_paths,
        cfg_strings=cfg_strings,
        cli_config=cli_config,
    )

    # Generate the compiled configuration for the simulation. This step also registers
    # the models required to run the simulation.
    configuration: CompiledConfiguration = generate_configuration(
        config_data.data, context={"cli_paths": cli_paths}
    )

    if progress > Progress.MINIMAL:
        print("* Configuration validated")

    if validate_only:
        return

    # Get the core configuration class
    core_configuration: CoreConfiguration = configuration.get_subconfiguration(
        "core", CoreConfiguration
    )

    # Set up and check data output
    output_config = core_configuration.data_output_options
    output_dir = Path(output_config.out_path)
    # Create output folder if it does not exist
    if not output_dir.exists():
        output_dir.mkdir()

    # Get the output Zarr store path
    zarr_store_path = output_dir / output_config.output_data_file_name
    if zarr_store_path.exists():
        raise ValueError(
            f"The output data file path already exists: {zarr_store_path!s}"
        )

    # Save the merged config if requested
    if output_config.save_compiled_configuration:
        outfile = output_dir / output_config.compiled_configuration_file_name
        # Export the merged configuration
        configuration.export_toml(outfile)

        if progress > Progress.MINIMAL:
            print(f"* Saved compiled configuration: {outfile}")

    # Build core elements
    core_components = CoreComponents(config=core_configuration)
    if progress > Progress.MINIMAL:
        print("* Built core model components")

    data = Data(grid=core_components.grid)
    data.load_data_config(config=core_configuration)
    if progress > Progress.MINIMAL:
        print("* Initial data loaded")

    # Setup the variables for the requested modules and verify consistency
    runtime_variables = setup_variables(
        models=list(configuration._model_classes.values()),
        data_vars=[str(v) for v in data.data],
        known_variables=data.known_variables,
    )

    LOGGER.info("All models found in the registry, now attempting to configure them.")

    # Check the variables to save
    if not output_config.variables_to_save:
        # Output all variables if the config is an empty list
        variables_to_save = tuple(runtime_variables.keys())
    else:
        unknown_variables = set(output_config.variables_to_save).difference(
            runtime_variables.keys()
        )
        if unknown_variables:
            raise ConfigurationError(
                f"Unknown names in 'variables_to_save': {','.join(unknown_variables)}"
            )
        variables_to_save = output_config.variables_to_save

    # Get the model initialisation sequence and initialise
    init_sequence = {
        model_name: configuration._model_classes[model_name]
        for model_name in get_model_order(
            stage="init", runtime_variables=runtime_variables
        )
    }

    models_init = initialise_models(
        configuration=configuration,
        data=data,
        core_components=core_components,
        models=init_sequence,
    )
    if progress > Progress.MINIMAL:
        print(f"* Models initialised: {', '.join(configuration._model_classes.keys())}")

    LOGGER.info("All models successfully initialised.")

    # Get disturbances order and initialise them
    if disturbance_config := configuration.get_disturbance_config():
        disturbances = initialise_disturbances(
            configuration=disturbance_config,
            data=data,
            core_components=core_components,
            models=models_init,
        )

        LOGGER.info("All disturbances successfully initialised.")
    else:
        disturbances = {}

    # TODO - A model spin up might be needed here in future

    # Identify which variables should be saved to the different zarr store groups:
    # - the 'inputs' group contains variables provided to the model
    # - the 'init' group contains variable states after model initialisation.
    # - the 'outputs' group contains the model values at each time step

    # Identify variable groups to save
    input_vars_to_save = [
        k
        for k in variables_to_save
        if runtime_variables[k].vars_populated_by_init == ["data"]
    ]
    init_vars_to_save = [
        k
        for k in variables_to_save
        if runtime_variables[k].vars_populated_by_init
        and runtime_variables[k].vars_populated_by_init != ["data"]
    ]
    output_vars_to_save = [
        k for k in variables_to_save if runtime_variables[k].vars_updated
    ]

    # Export any input and init vars now.
    for vars, group in ((input_vars_to_save, "inputs"), (init_vars_to_save, "init")):
        if vars:
            data.save_to_zarr(
                output_file_path=zarr_store_path, group=group, variables_to_save=vars
            )

    if progress > Progress.MINIMAL:
        print("* Initialisation data export complete.")

    # Take the models in their current execution sequence and change to the model update
    # sequence
    models_update = {
        model_name: models_init[model_name]
        for model_name in get_model_order(
            stage="update", runtime_variables=runtime_variables
        )
    }
    if progress > Progress.MINIMAL:
        print("* Starting simulation")

    # Setup the timing loop, adding a progress bar to print output. The output of the
    # progress bar is suppressed when progress is not set to Progress.FULL
    pbar = tqdm(
        total=core_components.model_timing.n_updates,
        file=sys.stdout,
        disable=progress < Progress.FULL,
    )
    time_index = 0
    current_time = core_components.model_timing.start_time
    while current_time < core_components.model_timing.end_time:
        LOGGER.info(f"Starting update {time_index}: {current_time}")

        current_time += core_components.model_timing.update_interval

        # Canary variable for model variable spec issues
        model_variables_ok = True

        # Run update() method for every model
        for model in models_update.values():
            data_vars_before_update = [str(i) for i in data.data.data_vars]
            model.update(time_index)
            data_vars_after_update = [str(i) for i in data.data.data_vars]

            # Check the variables added during the first update.
            if time_index == 0:
                check_added_variables(
                    before=data_vars_before_update,
                    after=data_vars_after_update,
                    claimed=model.vars_populated_by_first_update,
                    model=model.model_name,
                    attr="vars_populated_by_first_update",
                )

        for disturbance in disturbances.values():
            disturbance.disturb(time_index)

        # If there are mismatches in the variable specifications, fail.
        if not model_variables_ok:
            to_raise = RuntimeError("Model variable definitions inaccurate: check log.")
            LOGGER.critical(to_raise)
            raise to_raise

        # Append updated data to the output data store
        data.save_current_state_to_zarr(
            output_file_path=zarr_store_path,
            variables_to_save=output_vars_to_save,
            group="outputs",
            time_index=time_index,
            timestamp=core_components.model_timing.update_datestamps[time_index],
        )

        # Handle the debug option to truncate the run
        if (core_configuration.debug.truncate_run_at_update >= 0) & (
            core_configuration.debug.truncate_run_at_update == time_index
        ):
            msg = (
                f"Simulation truncated by core.debug.truncate_run_at_update at "
                f"index {core_configuration.debug.truncate_run_at_update}"
            )
            LOGGER.warning(msg)
            if progress > Progress.MINIMAL:
                print("* " + msg)
            break

        # With updates complete increment the time_index
        time_index += 1

        pbar.update(n=1)

    pbar.close()

    if progress > Progress.MINIMAL:
        print("* Simulation completed")

    LOGGER.info("Virtual Ecosystem model run completed!")

    # Restore default logging settings
    if logfile is not None:
        remove_file_logger()

    if progress > Progress.SILENT:
        print("Virtual Ecosystem run complete.")
