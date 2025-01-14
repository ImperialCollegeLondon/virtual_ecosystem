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

import json
import pkgutil
import sys
from collections.abc import Hashable
from dataclasses import asdict, dataclass, field
from graphlib import CycleError, TopologicalSorter
from importlib import import_module, resources
from pathlib import Path
from typing import cast

from jsonschema import FormatChecker
from tabulate import tabulate

import virtual_ecosystem.core.axes as axes
import virtual_ecosystem.core.base_model as base_model
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.schema import ValidatorWithDefaults

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def to_camel_case(snake_str: str) -> str:
    """Convert a snake_case string to CamelCase.

    Args:
        snake_str: The snake case string to convert.

    Returns:
        The camel case string.
    """
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


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
    populated_by_init: list[str] = field(default_factory=list, init=False)
    """Model that initialised the variable either in init or by input data."""
    populated_by_update: list[str] = field(default_factory=list, init=False)
    """Model that initialised the variable in its update method."""
    required_by_init: list[str] = field(default_factory=list, init=False)
    """Models that require the variable to be initialised."""
    updated_by: list[str] = field(default_factory=list, init=False)
    """Models that update the variable."""
    required_by_update: list[str] = field(default_factory=list, init=False)
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

    @property
    def related_models(self) -> set[str]:
        """Get all models that are related to the variable.

        Returns:
            The set of all models related to the variable.
        """
        all_models = (
            set(self.populated_by_init)
            | set(self.populated_by_update)
            | set(self.required_by_init)
            | set(self.updated_by)
            | set(self.required_by_update)
        )
        all_models.discard("data")
        return all_models


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


def _discover_models() -> list[type[base_model.BaseModel]]:
    """Discover all the models in Virtual Ecosystem."""
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

        mod_class_name = to_camel_case(mod.name) + "Model"
        if hasattr(module, mod_class_name):
            models_found.append(getattr(module, mod_class_name))
        else:
            LOGGER.warning(
                f"No model class '{mod_class_name}' found in module "
                f"'{models.__name__}.{mod.name}.{mod.name}_model'."
            )
            continue

    return models_found


def output_known_variables(output_file: Path) -> None:
    """Output the known variables to a file.

    For the variables to be output, the variables must be registered and the usage of
    the variables must be discovered, assigning the appropriate models to the variables.

    Args:
        output_file: The file to output the known variables to.
    """
    register_all_variables()

    models = _discover_models()
    _collect_vars_populated_by_init(models, check_unique_initialisation=False)
    _collect_vars_populated_by_first_update(models, check_unique_initialisation=False)

    # Add any variables that are not yet in the run registry to account for those
    # that would have been initialised by the data object.
    for name, var in KNOWN_VARIABLES.items():
        if name not in RUN_VARIABLES_REGISTRY:
            RUN_VARIABLES_REGISTRY[name] = var

    _collect_vars_required_for_init(models)
    _collect_updated_by_vars(models, check_unique_update=False)
    _collect_vars_required_for_update(models)

    vars = {
        var.name: asdict(var)
        for var in sorted(KNOWN_VARIABLES.values(), key=lambda x: x.name)
    }

    Path(output_file).with_suffix(".rst").write_text(_format_variables_list(vars))


def _format_variables_list(vars: dict[str, dict]) -> str:
    """Format the variables list for the RST output.

    Args:
        vars: The variables to format.

    Returns:
        The flist of variables and atrributes formated as a sequence of tables
        in RST format.
    """
    out = []
    for i, v in enumerate(vars.values()):
        title = f"{i + 1}- {v['name']}"
        out.append(title)
        out.append(f"{'=' * len(title)}")
        out.append("")
        out.append(tabulate(list(zip(v.keys(), v.values())), tablefmt="rst"))
        out.append("")

    return "\n".join(out)


def _collect_vars_populated_by_init(
    models: list[type[base_model.BaseModel]], check_unique_initialisation: bool = True
) -> None:
    """Initialise the runtime variable registry.

    It is a runtime error if a variable is initialised by more than one model. However,
    when this function is used to populate variable descriptions across known model - as
    in :func:`virtual_ecosystem.core.variables.output_known_variables` - alternative
    models may report initialising the same variable. The `check_unique_initialisation`
    flag is used to switch between these use cases.

    Args:
        models: The list of models that are initialising the variables.
        check_unique_initialisation: Fail on duplicate intialisation.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or if it is already initialised by another model.
    """
    for model in models:
        for var in model.vars_populated_by_init:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} is not in the"
                    " known variables registry."
                )
            if var in RUN_VARIABLES_REGISTRY and check_unique_initialisation:
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} already in "
                    f"registry as initialised by "
                    f"{RUN_VARIABLES_REGISTRY[var].populated_by_init}."
                )

            KNOWN_VARIABLES[var].populated_by_init.append(model.model_name)
            RUN_VARIABLES_REGISTRY[var] = KNOWN_VARIABLES[var]


def _collect_vars_populated_by_first_update(
    models: list[type[base_model.BaseModel]], check_unique_initialisation: bool = True
) -> None:
    """Initialise the runtime variable registry.

    It is a runtime error if a variable is initialised by more than one model. However,
    when this function is used to populate variable descriptions across known model - as
    in :func:`virtual_ecosystem.core.variables.output_known_variables` - alternative
    models may report initialising the same variable. The `check_unique_initialisation`
    flag is used to switch between these use cases.

    Args:
        models: The list of models that are initialising the variables.
        check_unique_initialisation: Fail on duplicate intialisation.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or if it is already initialised by another model.
    """
    for model in models:
        for var in model.vars_populated_by_first_update:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} is not in the"
                    " known variables registry."
                )
            if var in RUN_VARIABLES_REGISTRY and check_unique_initialisation:
                v = RUN_VARIABLES_REGISTRY[var]
                initialiser = (
                    v.populated_by_init[0]
                    if v.populated_by_init
                    else v.populated_by_update[0]
                )
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} already in "
                    f"registry as initialised by {initialiser}."
                )

            KNOWN_VARIABLES[var].populated_by_update.append(model.model_name)
            RUN_VARIABLES_REGISTRY[var] = KNOWN_VARIABLES[var]


def _collect_updated_by_vars(
    models: list[type[base_model.BaseModel]], check_unique_update: bool = True
) -> None:
    """Verify that all variables updated by models are in the runtime registry.

    Args:
        models: The list of models to check.
        check_unique_update: Fail on duplicate update.

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
            if len(RUN_VARIABLES_REGISTRY[var].updated_by) and check_unique_update:
                LOGGER.warning(
                    f"Variable {var} updated by {model.model_name} is already updated"
                    f" by {RUN_VARIABLES_REGISTRY[var].updated_by}."
                )
            RUN_VARIABLES_REGISTRY[var].updated_by.append(model.model_name)


def _collect_vars_required_for_update(models: list[type[base_model.BaseModel]]) -> None:
    """Verify that all variables required by the update methods are in the registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_required_for_update:
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
            RUN_VARIABLES_REGISTRY[var].required_by_update.append(model.model_name)


def _collect_vars_required_for_init(models: list[type[base_model.BaseModel]]) -> None:
    """Verify that all variables required by the init methods are in the registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_required_for_init:
            # TODO In the future, var will be a string, so this won't be necessary
            # var = v[0]
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
            RUN_VARIABLES_REGISTRY[var].required_by_init.append(model.model_name)


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
                f"{RUN_VARIABLES_REGISTRY[var].populated_by_init}."
            )

        KNOWN_VARIABLES[var].populated_by_init.append("data")
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
    # Variables related to the initialisation step
    _collect_initial_data_vars(cast(list[str], data_vars))
    _collect_vars_populated_by_init(models)
    _collect_vars_required_for_init(models)

    # Variables related to the update step
    _collect_vars_populated_by_first_update(models)
    _collect_updated_by_vars(models)
    _collect_vars_required_for_update(models)


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


def get_variable(name: str) -> Variable:
    """Get the variable by name.

    Args:
        name: The name of the variable to get.

    Returns:
        The variable with the given name.

    Raises:
        KeyError: If the variable is not in the run variables registry, whether known
            or unknown to Virtual Ecosystem.
    """
    if var := RUN_VARIABLES_REGISTRY.get(name):
        return var

    if name in KNOWN_VARIABLES:
        raise KeyError(
            f"Variable '{name}' is a known variable but is not initialised by any model"
            " or provided as input data in this run."
        )
    else:
        raise KeyError(f"Variable '{name}' is not a known variable.")


def get_model_order(stage: str) -> list[str]:
    """Get the order of running the models during init or update.

    This order is based on the dependencies of initialisation and update of the
    variables.

    Args:
        stage: The stage of the simulation to get the order for. It must be either
            "init" or "update".

    Returns:
        The order of initialisation of the variables.
    """
    if stage not in ("init", "update"):
        raise ConfigurationError("Stage must be either 'init' or 'update'.")

    depends: dict[str, set] = {}
    for var in RUN_VARIABLES_REGISTRY.values():
        depends.update(
            {model: set() for model in var.related_models if model not in depends}
        )

        # If the variable does not impose a dependency, skip it
        if (stage == "init" and not var.populated_by_init) or (
            stage == "update" and not var.populated_by_update
        ):
            continue

        initialiser = (
            var.populated_by_init[0] if stage == "init" else var.populated_by_update[0]
        )

        # If the variable is initialised by the data object, it does not impose a
        # dependency, so skip it as well
        if initialiser == "data":
            continue

        required_by = (
            var.required_by_init if stage == "init" else var.required_by_update
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
