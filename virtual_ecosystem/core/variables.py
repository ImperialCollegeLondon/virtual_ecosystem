"""Variable validation and model checking.

Variables are defined in the ``data_variables.toml`` file in the root folder of
``virtual_ecosystem`` . When the model runs, this data is loaded into the
:attr:`Data.known_variables<virtual_ecosystem.core.data.Data.known_variables>`
attribute, using the :meth:`load_known_variables` function is this module. The attribute
provides a dictionary, keyed by variable name, of
:class:`~virtual_ecosystem.core.variables.VariableMetadata` instances, which hold
the metadata loaded from file. That data is used to:

    * Check that only known variables are added to the Data instance.
    * Check that variable axes are defined correctly.
    * Add variable metadata, such as units and description, to output files.

The ``VariableMetadata`` instances also have attributes that are used to track which
variables appear in the various ``var_...`` attributes of the set of running models.
This is used to build up a dictionary of variables used by a particular simulation run
(runtime variables) that tracks variable usage during runtime:

    * What variables are initialised from data or by models, and are they uniquely
      initialised.
    * Are variables required by models initialised by other models?
    * Are there running orders for both model initialisation and update that
      avoid circular variable dependencies.

To add a new variable, simply edit the ``data_variables.toml`` file and add the variable
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

from pydantic import (
    BaseModel as PydanticBaseModel,
)
from pydantic import (
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic.dataclasses import dataclass as py_dataclass

from virtual_ecosystem.core.axes import AXIS_VALIDATORS
from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


@py_dataclass
class VariableMetadata:
    """Variable metadata class.

    This class is used to both validate entries loaded from a variables metadata
    file and to provide attributes that are used to track how each variable is used by
    the different models at runtime. The ``axis`` attribute has additional validation
    applied after loading to check that it values are unique and valid.
    """

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
    """Used at runtime to track which models require the variable to be initialised."""
    vars_populated_by_init: list[str] = Field(init=False, default=[])
    """Used at runtime to track whether the variable is initialised from input data or
    during the initialisation stage of one of the models."""
    vars_required_by_update: list[str] = Field(init=False, default=[])
    """Used at runtime to track which models use the variable."""
    vars_populated_by_first_update: list[str] = Field(init=False, default=[])
    """Used at runtime to track which model initialises the variable during the update
    stage."""
    vars_updated: list[str] = Field(init=False, default=[])
    """Used at runtime to track which models update the variable."""

    @field_validator("axis", mode="after")
    def unique_axes(cls, value: list[str], info: ValidationInfo) -> list[str]:
        """Check axis list entries are unique and known."""

        if len(value) != len(set(value)):
            raise ValueError(
                f"Axis values not unique in variable: {info.data['name']}."
            )

        unknown_axes = sorted(set(value).difference(AXIS_VALIDATORS.keys()))

        if unknown_axes:
            raise ValueError(
                f"Variable {info.data['name']} uses unknown "
                f"axes: {','.join(unknown_axes)}"
            )

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


class VariablesFile(PydanticBaseModel):
    """Validation class for a variable definitions file.

    This validator loads a variable definitions file, following the format used in
    ``data_variables.toml``, applying validation to each entry, and then checks that the
    file does not contain duplicate variable definitions.
    """

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


def load_known_variables(
    variable_file: str | None = None,
) -> dict[str, VariableMetadata]:
    """Loads variables from a TOML variable database file.

    The contents of the file are loaded using tomllib and then passed to the
    :class:`VariablesFile` validation class, which in turn applies the
    :class:`VariableMetadata` validation class to each entry.

    Args:
        variable_file: The path to a variables file.

    Returns:
        A dictionary, keyed by variable name, of validated ``VariableMetadata``
        instances.
    """

    # Default to the main variables file.
    if variable_file is None:
        variable_file = str(
            resources.files("virtual_ecosystem") / "data_variables.toml"
        )

    with open(variable_file, "rb") as f:
        known_vars = tomllib.load(f)

    validated = VariablesFile.model_validate(known_vars)

    return {v.name: v for v in validated.variable}


def setup_variables(
    models: list[type[BaseModel]],
    data_vars: list[str],
    known_variables: dict[str, VariableMetadata],
) -> dict[str, VariableMetadata]:
    """Generate the runtime variables dictionary.

    This function takes the data variables provided by the initial data and a
    list of requested science models and populates a dictionary of runtime variables.
    The function then:

    * Checks that all variables provided in the data or appearing in model definitions
      appear in the dictionary of known variables.
    * Populates the model usage attributes of the variables being used at runtime,
      including initial checking that:

        * variables are uniquely initialised,
        * required variables have been initialised by a model or from data,

    Note that the called functions all update the ``runtime_variables`` dictionary by
    reference. This is used because - in addition to adding new variables - the
    functions are updating attributes of existing runtime variables. It is much more
    concise to update by reference here rather than passing update information back to
    this function.

    Args:
        models: The list of models to setup variables for.
        data_vars: The list of variables defined in the data object.
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If: a variable required by a model is not in the known variables; a
            variable is required but not populated; a variable is initialised more than
            once.
    """

    runtime_variables: dict[str, VariableMetadata] = {}

    # Variables related to the initialisation step
    _collect_initial_data_vars(
        vars=data_vars,
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )

    # Check all the variables in the models are present in known variables
    _check_model_variables_are_known(models, known_variables)

    # Variables related to the init step
    _collect_vars_populated_by_init(
        models=models,
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )
    _collect_vars_required_for_init(
        models=models,
        runtime_variables=runtime_variables,
    )

    # Variables related to the update step
    _collect_vars_populated_by_first_update(
        models=models,
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )
    _collect_vars_updated(
        models=models,
        runtime_variables=runtime_variables,
    )
    _collect_vars_required_for_update(
        models=models,
        runtime_variables=runtime_variables,
    )

    return runtime_variables


def _collect_initial_data_vars(
    vars: list[str],
    runtime_variables: dict[str, VariableMetadata],
    known_variables: dict[str, VariableMetadata],
) -> None:
    """Collects the variables defined in the data object.

    The ``runtime_variables`` dictionary is updated in place to add variables provided
    in the initial data.

    Args:
        vars: The list of variables defined in the data object.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: if a provided variable is unknown or is already present in the
            runtime variables dictionary.
    """
    for var in vars:
        if var not in known_variables:
            raise ValueError(f"Unknown variable {var} in data object")

        if var in runtime_variables:
            raise ValueError(f"Variable {var} already populated from data")

        runtime_variables[var] = known_variables[var]
        runtime_variables[var].vars_populated_by_init.append("data")


def _check_model_variables_are_known(
    models: list[type[BaseModel]], known_variables: dict[str, VariableMetadata]
):
    """Checks the model variables are known.

    This function iterates over the provided models and checks that all of the variables
    listed in the variable usage attributes are present in a dictionary of known
    variables.

    Args:
        models: The list of models that are initialising the variables.
        known_variables: A dictionary of known variables

    Raises:
        ValueError: if an unknown variable appears in a model variable usage attribute.
    """

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
                    f"Unknown variables in {mod.model_name}.{var_attr}: "
                    f"{', '.join(unknown_variables)}"
                )
                fail = True

    if fail:
        msg = f"Model {mod.model_name} definition contains unknown variables, check log"
        LOGGER.critical(msg)
        raise ValueError(msg)


def _collect_vars_populated_by_init(
    models: list[type[BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
    known_variables: dict[str, VariableMetadata],
) -> None:
    """Adds variables populated by model initialisation to the runtime variables.

    This function adds variables appearing in the ``vars_populated_by_init`` attribute
    of each model to the runtime variable dictionary, adding the model name to the
    :attr:`VariableMetadata.vars_populated_by_init` attribute of the variable.

    The ``runtime_variables`` dictionary is updated in place to add variables provided
    in the initial data.

    Args:
        models: The list of models that are initialising the variables.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable is already initialised by another model or by initial
            data .
    """
    for model in models:
        for var in model.vars_populated_by_init:
            if var in runtime_variables:
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} already "
                    f"initialised by {runtime_variables[var].vars_populated_by_init}."
                )

            runtime_variables[var] = known_variables[var]
            runtime_variables[var].vars_populated_by_init.append(model.model_name)


def _collect_vars_required_for_init(
    models: list[type[BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
) -> None:
    """Checks variables required for model initialisation.

    The function checks that all variables appearing in the ``vars_required_for_init``
    attribute of each model has been added to the dictionary of runtime variables as
    being initialised from data or by a model. It updates the runtime variables
    dictionary to add model names to the :attr:`VariableMetadata.vars_required_for_init`
    attribute for each variable.

    The ``runtime_variables`` dictionary is updated in place to record which models
    require each variable for initialisation.

    Args:
        models: The list of models to check.
        runtime_variables: A dictionary of variables being used in this runtime

    Raises:
        ValueError: If a variable required by a model for initialisation has not been
            initialised from data or by a model.
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
    models: list[type[BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
    known_variables: dict[str, VariableMetadata],
) -> None:
    """Adds variables populated by model first update to the runtime variables.

    This function adds variables appearing in the ``vars_populated_by_first_update``
    attribute of each model to the runtime variable dictionary, adding the model name to
    the :attr:`VariableMetadata.vars_populated_by_first_update` attribute of the
    variable.

    The ``runtime_variables`` dictionary is updated in place to add variables provided
    in the initial data.

    Args:
        models: The list of models that are initialising the variables.
        runtime_variables: A dictionary of variables being used in this runtime
        known_variables: A dictionary of known variables

    Raises:
        ValueError: If a variable is already initialised by another model, at either
            model initialisation or update, or from initial data.
    """
    for model in models:
        for var in model.vars_populated_by_first_update:
            if var in runtime_variables:
                v = runtime_variables[var]
                init_model, init_stage = (
                    (v.vars_populated_by_init[0], "init")
                    if v.vars_populated_by_init
                    else (v.vars_populated_by_first_update[0], "first update")
                )
                raise ValueError(
                    f"Variable {var} initialised by {model.model_name} already "
                    f"initialised during {init_stage} by {init_model}."
                )

            runtime_variables[var] = known_variables[var]
            runtime_variables[var].vars_populated_by_first_update.append(
                model.model_name
            )


def _collect_vars_updated(
    models: list[type[BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
) -> None:
    """Checks variables updated by models.

    The function checks that all variables appearing in the ``vars_updated`` attribute
    of each model are initialised by data or a model. It adds the model name to the
    :attr:`VariableMetadata.vars_updated` attribute of each variable.

    The ``runtime_variables`` dictionary is updated in place to record which models
    require each variable for initialisation.

    The function emits a log warning if more than one model updates a variable.

    Args:
        models: The list of models to check.
        runtime_variables: A dictionary of variables being used in this runtime

    Raises:
        ValueError: If a variable has not been initialised.
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
    models: list[type[BaseModel]],
    runtime_variables: dict[str, VariableMetadata],
) -> None:
    """Checks variables required for model updates.

    The function checks that all variables appearing in the ``vars_required_for_update``
    attribute of each model are initialised by data or a model. It adds the model name
    to the :attr:`VariableMetadata.vars_required_for_update` attribute of each variable.

    The ``runtime_variables`` dictionary is updated in place to record which models
    require each variable for initialisation.

    Args:
        models: The list of models to check.
        runtime_variables: A dictionary of variables being used in this runtime

    Raises:
        ValueError: If a variable has not been initialised..
    """

    for model in models:
        for var in model.vars_required_for_update:
            if var not in runtime_variables:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model neither provided as input."
                )
            runtime_variables[var].vars_required_by_update.append(model.model_name)


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
