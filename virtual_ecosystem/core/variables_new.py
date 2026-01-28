"""Module for all variables.

Variables are defined in the `data_variables.toml` file, in the root folder of
`virtual_ecosystem `, which is loaded at runtime and validated. Variables are then
registered in the `KNOWN_VARIABLES` registry. The usage of the variables is then
discovered by checking the models for the different methods that the variables are
used (initialisation, update, etc.).

The variables actually used by the models in a run are then registered in the global
`RUN_VARIABLES_REGISTRY` registry. The subset of the variables are checked to ensure
the consistency of the simulation (eg. all variables required by a model are initialised
by another model, all axis needed by the variables are defined, etc.).

To add a new variable, simply edit the `data_variables.toml` file and add the variable
as:

.. code-block:: toml

    [[variable]]
    name = "variable_name"
    description = "Description of the variable."
    unit = "Unit of the variable."
    variable_type = "Type of the variable."
    axis = ["axis1", "axis2"]

where `axis1` and `axis2` are the name of axis validators defined
on :mod:`~virtual_ecosystem.core.axes`.
"""

from __future__ import annotations

import tomllib
from collections import Counter
from graphlib import CycleError, TopologicalSorter
from importlib import resources

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.dataclasses import dataclass as py_dataclass

import virtual_ecosystem.core.axes as axes
import virtual_ecosystem.core.base_model as base_model
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


def to_camel_case(snake_str: str) -> str:
    """Convert a snake_case string to CamelCase.

    Args:
        snake_str: The snake case string to convert.

    Returns:
        The camel case string.
    """
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


@py_dataclass
class VariableMetadata:
    """Validator class for entries in the variables metadata file."""

    name: str
    """Name of the variable. Must be unique."""
    description: str
    """Description of what the variable represents."""
    unit: str
    """Units the variable should be represented in."""
    variable_type: str
    """Type of the variable."""
    axis: list[str]
    """Axes the variable is defined on."""
    vars_required_by_init: list[str] = Field(init=False, default=[])
    """Models that require the variable to be initialised."""
    vars_populated_by_init: list[str] = Field(init=False, default=[])
    """Model that initialised the variable either in init or by input data."""
    vars_required_by_update: list[str] = Field(init=False, default=[])
    """Models that use the variable."""
    vars_populated_by_first_update: list[str] = Field(init=False, default=[])
    """Model that initialised the variable in its update method."""
    vars_updated: list[str] = Field(init=False, default=[])
    """Models that update the variable."""

    @field_validator("axis")
    def unique_axes(cls, value: list[str]) -> list[str]:
        """Check axis list entries are unique."""

        if len(value) != len(set(value)):
            raise ValueError("Axis values not unique.")

        return value

    @property
    def related_models(self) -> set[str]:
        """Get all models that are related to the variable.

        Returns:
            The set of all models related to the variable.
        """
        all_models = (
            set(self.vars_required_by_init)
            | set(self.vars_populated_by_init)
            | set(self.vars_required_by_update)
            | set(self.vars_populated_by_first_update)
            | set(self.vars_updated)
        )
        all_models.discard("data")
        return all_models


class VariablesFile(BaseModel):
    """Validation class for the variables.toml file."""

    variable: list[VariableMetadata] = []

    @model_validator(mode="after")
    def _names_unique(self) -> VariablesFile:
        """Model validation that the variable names are unique."""

        names = [var.name for var in self.variable]
        names_count = Counter(names)

        duplicated = [n for n, c in names_count.items() if c > 1]
        if duplicated:
            raise ValueError(
                f"Duplicate variable names in variables file: {','.join(duplicated)}"
            )

        return self


def load_known_variables() -> dict[str, VariableMetadata]:
    """Loads the known variables from the variable database.

    The pydantic classes handle validation of the input.
    """

    with open(
        str(resources.files("virtual_ecosystem") / "data_variables.toml"), "rb"
    ) as f:
        known_vars = tomllib.load(f)

    validated = VariablesFile.model_validate(known_vars)

    return {v.name: v for v in validated.variable}


def setup_variables(
    models: list[type[base_model.BaseModel]],
    data_vars: list[str],
    known_variables: dict[str, VariableMetadata],
) -> dict[str, VariableMetadata]:
    """Setup the runtime variable registry, running some validation.

    Args:
        models: The list of models to setup the registry for.
        data_vars: The list of variables defined in the data object.
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """

    runtime_variables: dict[str, VariableMetadata] = {}

    # Check all the variables in the models are present in known variables
    _check_model_variables_are_known(models, known_variables)

    # Variables related to the initialisation step
    _collect_initial_data_vars(
        vars=data_vars,
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )

    _collect_vars_populated_by_init(
        models=models,
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )
    _collect_vars_required_for_init(
        models,
        runtime_variables=runtime_variables,
    )

    # Variables related to the update step
    _collect_vars_populated_by_first_update(
        models,
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )
    _collect_updated_by_vars(
        models,
        runtime_variables=runtime_variables,
    )
    _collect_vars_required_for_update(
        models,
        runtime_variables=runtime_variables,
    )

    return runtime_variables


def _check_model_variables_are_known(models, known_variables):
    variable_attributes = (
        "vars_required_for_init",
        "vars_populated_by_init",
        "vars_required_for_update",
        "vars_populated_by_first_update",
        "vars_updated",
    )

    fail = False

    for mod in models:
        for var_attr in variable_attributes:
            unknown_variables = set(getattr(mod, var_attr)).difference(known_variables)

            if unknown_variables:
                LOGGER.error(
                    f"Unknown variables in {mod.name}.{var_attr}: "
                    f"{', '.join(unknown_variables)}"
                )
                fail = True

    if fail:
        msg = "Model configuration contains unknown variables, check log"
        LOGGER.critical(msg)
        raise ValueError(msg)


def _collect_initial_data_vars(
    vars: list[str],
    runtime_variables: dict[str, VariableMetadata],
    known_variables: dict[str, VariableMetadata],
) -> None:
    """Collects the variables defined in the data object.

    Args:
        vars: The list of variables defined in the data object.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables
    """
    for var in vars:
        runtime_variables[var] = known_variables[var]
        runtime_variables[var].vars_populated_by_init.append("data")


def _collect_vars_populated_by_init(
    models: list[type[base_model.BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
    known_variables: dict[str, VariableMetadata],
) -> None:
    """Initialise the runtime variable registry.

    It is a runtime error if a variable is initialised by more than one model.

    Args:
        models: The list of models that are initialising the variables.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or if it is already initialised by another model.
    """
    for model in models:
        for var in model.vars_populated_by_init:
            if var in runtime_variables:
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} already in "
                    f"registry as initialised by "
                    f"{runtime_variables[var].vars_populated_by_init}."
                )

            runtime_variables[var] = known_variables[var]
            runtime_variables[var].vars_populated_by_init.append(model.model_name)


def _collect_vars_required_for_init(
    models: list[type[base_model.BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
) -> None:
    """Verify that all variables required by the init methods are in the registry.

    Args:
        models: The list of models to check.
        runtime_variables: A dictionary of variables being used in this runtime

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_required_for_init:
            if var not in runtime_variables:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} during "
                    "initialisation is not initialised by any model neither provided as"
                    " input."
                )
            runtime_variables[var].vars_required_by_init.append(model.model_name)


def _collect_vars_populated_by_first_update(
    models: list[type[base_model.BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
    known_variables: dict[str, VariableMetadata],
) -> None:
    """Initialise the runtime variable registry.

    It is a runtime error if a variable is initialised by more than one model. However,
    when this function is used to populate variable descriptions across known model - as
    in :func:`virtual_ecosystem.core.variables.output_known_variables` - alternative
    models may report initialising the same variable. The `check_unique_initialisation`
    flag is used to switch between these use cases.

    Args:
        models: The list of models that are initialising the variables.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or if it is already initialised by another model.
    """
    for model in models:
        for var in model.vars_populated_by_first_update:
            if var in runtime_variables:
                v = runtime_variables[var]
                initialiser = (
                    v.vars_populated_by_init[0]
                    if v.vars_populated_by_init
                    else v.vars_populated_by_first_update[0]
                )
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} already in "
                    f"registry as initialised by {initialiser}."
                )

            runtime_variables[var] = known_variables[var]
            runtime_variables[var].vars_populated_by_first_update.append(
                model.model_name
            )


def _collect_updated_by_vars(
    models: list[type[base_model.BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
) -> None:
    """Verify that all variables updated by models are in the runtime registry.

    Args:
        models: The list of models to check.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_updated:
            if var not in runtime_variables:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model."
                )
            if len(runtime_variables[var].vars_updated):
                LOGGER.warning(
                    f"Variable {var} updated by {model.model_name} is already updated"
                    f" by {runtime_variables[var].vars_updated}."
                )

            runtime_variables[var].vars_updated.append(model.model_name)


def _collect_vars_required_for_update(
    models: list[type[base_model.BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
) -> None:
    """Verify that all variables required by the update methods are in the registry.

    Args:
        models: The list of models to check.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_required_for_update:
            if var not in runtime_variables:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model neither provided as input."
                )
            runtime_variables[var].vars_required_by_update.append(model.model_name)


def verify_variables_axis(runtime_variables) -> None:
    """Verify that all required variables have valid, available axis."""
    for var in runtime_variables.values():
        unknown_axes = sorted(set(var.axis).difference(axes.AXIS_VALIDATORS.keys()))

        if unknown_axes:
            to_raise = ValueError(
                f"Variable {var.name} uses unknown axis: {','.join(unknown_axes)}"
            )
            LOGGER.error(to_raise)
            raise to_raise


def get_model_order(
    stage: str, runtime_variables: dict[str, VariableMetadata]
) -> list[str]:
    """Get the order of running the models during init or update.

    This order is based on the dependencies of initialisation and update of the
    variables.

    Args:
        stage: The stage of the simulation to get the order for. It must be either
            "init" or "update".
        runtime_variables: A dictionary of variables being used in this runtime

    Returns:
        The order of initialisation of the variables.
    """
    if stage not in ("init", "update"):
        raise ConfigurationError("Stage must be either 'init' or 'update'.")

    depends: dict[str, set] = {}
    for var in runtime_variables.values():
        depends.update(
            {model: set() for model in var.related_models if model not in depends}
        )

        # If the variable does not impose a dependency, skip it
        if (stage == "init" and not var.vars_populated_by_init) or (
            stage == "update" and not var.vars_populated_by_first_update
        ):
            continue

        initialiser = (
            var.vars_populated_by_init[0]
            if stage == "init"
            else var.vars_populated_by_first_update[0]
        )

        # If the variable is initialised by the data object, it does not impose a
        # dependency, so skip it as well
        if initialiser == "data":
            continue

        required_by = (
            var.vars_required_by_init
            if stage == "init"
            else var.vars_required_by_update
        )

        for dep in required_by:
            depends[dep].add(initialiser)

    sorter = TopologicalSorter(depends)

    # Find a resolved execution order, checking for cyclic dependencies.
    try:
        resolved_order: list[str] = list(sorter.static_order())
    except CycleError as excep:
        to_raise = f"Model {stage} dependencies are cyclic: {', '.join(excep.args[1])}"
        LOGGER.critical(to_raise)
        raise ConfigurationError(to_raise)

    LOGGER.info(f"Model {stage} execution order set: {', '.join(resolved_order)}")
    return resolved_order
