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

import inspect
import json
import pkgutil
import sys
from collections.abc import Hashable
from dataclasses import asdict, dataclass, field
from importlib import import_module, resources
from pathlib import Path
from typing import cast

import tomli_w
from jsonschema import FormatChecker

import virtual_ecosystem.core.axes as axes
import virtual_ecosystem.core.base_model as base_model
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.schema import ValidatorWithDefaults

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class Variable:
    """Simulation variable, containing static and runtime metadata."""

    name: str
    """Name of the variable. Must be unique."""
    description: str
    """Description of what the variable represents."""
    unit: str
    """Units the variable should be represented in."""
    variable_type: str
    """Type of the variable."""
    axis: tuple[str, ...]
    """Axes the variable is defined on."""
    initialised_by: str = field(default_factory=str, init=False)
    """Model that initialised the variable."""
    required_init_by: list[str] = field(default_factory=list, init=False)
    """Models that requires the variable to be initialised."""
    updated_by: list[str] = field(default_factory=list, init=False)
    """Models that update the variable."""
    required_update_by: list[str] = field(default_factory=list, init=False)
    """Models that use the variable."""

    def __post_init__(self) -> None:
        """Register the variable in the known variables.

        Raises:
            ValueError: If a variable is already in the known variables registry.
        """
        if self.name in KNOWN_VARIABLES:
            raise ValueError(
                f"Variable {self.name} already in the known variables registry."
            )

        KNOWN_VARIABLES[self.name] = self


RUN_VARIABLES_REGISTRY: dict[str, Variable] = {}
"""The global registry of variables used in a run."""

KNOWN_VARIABLES: dict[str, Variable] = {}
"""The global known variable registry."""


def register_all_variables() -> None:
    """Registers all variables provided by the models."""
    with open(
        str(resources.files("virtual_ecosystem") / "data_variables.toml"), "rb"
    ) as f:
        known_vars = tomllib.load(f).get("variable", [])

    with (resources.files("virtual_ecosystem.core") / "variables_schema.json").open(
        "r"
    ) as f:
        schema = json.load(f)

    val = ValidatorWithDefaults(schema, format_checker=FormatChecker())
    val.validate(known_vars)

    for var in known_vars:
        Variable(**var)


def _discover_all_variables_usage() -> None:
    """Discover the usage of variables in the models."""
    import virtual_ecosystem.models as models

    models_found = []
    for mod in pkgutil.iter_modules(models.__path__):
        if not mod.ispkg:
            continue

        try:
            module = import_module(f"{models.__name__}.{mod.name}.{mod.name}_model")
        except ImportError:
            LOGGER.warning(
                f"No model file found for model {models.__name__}.{mod.name}."
            )
            continue

        models_found.extend(
            [
                obj
                for _, obj in inspect.getmembers(module)
                if inspect.isclass(obj)
                and issubclass(obj, base_model.BaseModel)
                and obj is not base_model.BaseModel
            ]
        )

    setup_variables(models_found, [])


def output_known_variables(output_file: Path) -> None:
    """Output the known variables to a file.

    For the variables to be output, the variables must be registered and the usage of
    the variables must be discovered, assigning the appropriate models to the variables.

    Args:
        output_file: The file to output the known variables to.
    """
    register_all_variables()
    _discover_all_variables_usage()
    vars = {
        var.name: asdict(var)
        for var in sorted(KNOWN_VARIABLES.values(), key=lambda x: x.name)
    }
    with open(output_file, "bw") as f:
        tomli_w.dump(vars, f)


def _collect_initialise_by_vars(models: list[type[base_model.BaseModel]]) -> None:
    """Initialise the runtime variable registry.

    Args:
        models: The list of models that are initialising the variables.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or if it is already initialised by another model.
    """
    for model in models:
        for var in model.vars_initialised:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the"
                    " known variables registry."
                )
            if var in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var} already in registry, initialised by"
                    f"{RUN_VARIABLES_REGISTRY[var].initialised_by}."
                )

            KNOWN_VARIABLES[var].initialised_by = model.model_name
            RUN_VARIABLES_REGISTRY[var] = KNOWN_VARIABLES[var]


def _collect_updated_by_vars(models: list[type[base_model.BaseModel]]) -> None:
    """Verify that all variables updated by models are in the runtime registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_updated:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the known"
                    " variables registry."
                )
            if var not in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model."
                )
            if len(RUN_VARIABLES_REGISTRY[var].updated_by):
                LOGGER.warning(
                    f"Variable {var} updated by {model.model_name} is already updated"
                    f" by {RUN_VARIABLES_REGISTRY[var].updated_by}."
                )
            RUN_VARIABLES_REGISTRY[var].updated_by.append(model.model_name)


def _collect_required_update_vars(models: list[type[base_model.BaseModel]]) -> None:
    """Verify that all variables required by the update methods are in the registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.required_update_vars:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the known"
                    " variables registry."
                )
            if var not in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model neither provided as input."
                )
            RUN_VARIABLES_REGISTRY[var].required_update_by.append(model.model_name)


def _collect_required_init_vars(models: list[type[base_model.BaseModel]]) -> None:
    """Verify that all variables required by the init methods are in the registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for v in model.required_init_vars:
            # TODO In the future, var will be a string, so this won't be necessary
            var = v[0]
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the known"
                    " variables registry."
                )
            if var not in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} during "
                    "initialisation is not initialised by any model neither provided as"
                    " input."
                )
            RUN_VARIABLES_REGISTRY[var].required_init_by.append(model.model_name)


def _collect_initial_data_vars(vars: list[str]) -> None:
    """Collects the variables defined in the data object.

    Args:
        vars: The list of variables defined in the data object.
    """
    for var in vars:
        if var not in KNOWN_VARIABLES:
            raise ValueError(f"Variable {var} defined in data object is not known.")

        if var in RUN_VARIABLES_REGISTRY:
            raise ValueError(
                f"Variable {var} already in registry, initialised by"
                f"{RUN_VARIABLES_REGISTRY[var].initialised_by}."
            )

        KNOWN_VARIABLES[var].initialised_by = "data"
        RUN_VARIABLES_REGISTRY[var] = KNOWN_VARIABLES[var]


def setup_variables(
    models: list[type[base_model.BaseModel]], data_vars: list[Hashable]
) -> None:
    """Setup the runtime variable registry, running some validation.

    Args:
        models: The list of models to setup the registry for.
        data_vars: The list of variables defined in the data object.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    _collect_initial_data_vars(cast(list[str], data_vars))
    _collect_initialise_by_vars(models)
    _collect_required_init_vars(models)
    _collect_updated_by_vars(models)
    _collect_required_update_vars(models)


def verify_variables_axis() -> None:
    """Verify that all required variables have valid, available axis."""
    for var in RUN_VARIABLES_REGISTRY.values():
        unknown_axes = sorted(set(var.axis).difference(axes.AXIS_VALIDATORS.keys()))

        if unknown_axes:
            to_raise = ValueError(
                f"Variable {var.name} uses unknown axis: {','.join(unknown_axes)}"
            )
            LOGGER.error(to_raise)
            raise to_raise
