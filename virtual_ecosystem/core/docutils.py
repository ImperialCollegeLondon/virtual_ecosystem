"""This submodule contains a dataclass used to generate content for the documentation.
None of the functions defined here are intended for use outside of the documentation.
"""  # noqa: D205

import tomllib
from copy import deepcopy
from importlib import resources
from textwrap import indent

import dominate.tags as dt
import tomli_w
from IPython.display import display_markdown
from pydantic._internal._model_construction import ModelMetaclass
from pydantic_core import PydanticUndefined

from virtual_ecosystem.core.base_model import _discover_models
from virtual_ecosystem.core.configuration import Configuration

RST_TO_MD = [
    (":cite:t:", "{cite:t}"),
    (":cite:p:", "{cite:p}"),
    (":attr:", "{attr}"),
]
"""Tags to replace when converting RST descriptions of fields to Markdown."""


def dump_config_toml(path: str, config_object: Configuration) -> None:
    """Render a configuration class as TOML.

    This function returns markdown providing a styled TOML representation of a
    Configuration subclass, including default values.

    Args:
        path: The configuration path to the specified configuration class.
        config_object: A configuration class instance to render as TOML.
    """

    conf_dict = config_object.model_dump(mode="json")

    for p in reversed(path.split(".")):
        conf_dict = {p: conf_dict}

    display_markdown("```toml\n" + tomli_w.dumps(conf_dict) + "```", raw=True)


def model_config_to_deflist(
    model_name: str,
    config_object: Configuration,
    display: bool = True,
    recurse: bool = True,
):
    """Renders the fields in a configuration class as Myst Markdown definition list.

    This is a helper function for use in documenting model configurations. It takes a
    model configuration class and then iterates over model fields, recursing into
    sub-models within the fields if needed, to generate a definition list in MyST
    markdown.

    Using this requires that the markdown document in which the output is rendered sets
    ``mystnb`` parsing to use ``render_markdown_format: myst``. Myst parsing applies the
    class `myst` to the containing DL tags - the CSS of the DD and DT tags are extended
    by ``docs/source/_static/css/custom.css``.

    Args:
        model_name: The name of the model as it would appear in a configuration file.
        config_object: A ModelConfig instance
        display: Should the function wrap the output using display_markdown() or simply
            return the markdown text to be incorporated during recursion.
        recurse: Should the function recurse into nested models.
    """

    definitions = ""

    # Iterate over the model fields
    for name, field_info in config_object.model_fields.items():
        # Track the nested name of the field
        field_name = model_name + "." + name

        if isinstance(field_info.annotation, ModelMetaclass):
            # If the field is itself a model, then this is a nested section, so recurse
            # into the model if requested and then append the collected definitions to
            # the parent definitions
            if recurse:
                definitions += model_config_to_deflist(
                    field_name, field_info.annotation, display=False
                )

        else:
            # Otherwise, get the default value (or not) for the field
            default = field_info.get_default(call_default_factory=True)

            if default is PydanticUndefined:
                default_string = "No default"
            else:
                default_string = f"Default = {default!s}"

            if field_info.description is None:
                description = "Field description missing."
            else:
                description = field_info.description
                for rst, md in RST_TO_MD:
                    description = description.replace(rst, md)

            # Indent the description to nest it all within the dd header, but set the
            # first character on the first line as a colon to define it as the
            # description.
            description = indent(description + " " + default_string, prefix="  ")
            description = ":" + description[1:]

            definitions += f"{field_name}\n{description}\n\n"

    if not display:
        return definitions

    return display_markdown(definitions, raw=True)


def variable_table():
    """Generate an HTML TABLE representation of the data variables.

    This function returns HTML with the following elements:

    * A DIV containing checkbox selectors for each registered model (apart from the toy
      testing model).
    * A DIV containing checkbox selectors for each role from the model variable class
      attributes.
    * A TABLE element containing the variable name, description, axes, units and then
      which models include each variable in each role.

        *   0: Column used to hold DataTables dt-control to hide/show child cells
        *   1: 'name', Name
        *   2: 'unit', Units
        *   3: 'axis', Axes
        *   4: 'description', Description
        *   5: 'variable_type', Variable Type
        *   6: 'vars_required_for_init', RI
        *   7: 'vars_populated_by_init', PI
        *   8: 'vars_required_for_update' RU
        *   9: 'vars_populated_by_first_update', PU
        *  10: 'vars_updated', Updated

    The sphinx configuration is then setup to add JavaScript to the page displaying this
    table that adds DataTable functionality to the TABLE object and implements filtering
    using the checkboxes. It also hides the columns containing the model by variable
    role data - this is inferred from the selector checkbox settings.
    """

    # Get the full set of models
    models = [m for m in _discover_models() if m.model_name != "testing"]

    # Load the full set of data variables
    with open(
        str(resources.files("virtual_ecosystem") / "data_variables.toml"), "rb"
    ) as f:
        source_vars = tomllib.load(f)["variable"]

    # Define a map of model variable attributes onto field names and create a template
    # dictionary to record the stages at which each model interacts with the different
    # variables.
    model_var_attribute_fields = (
        ("vars_required_for_init", "Req. Init"),
        ("vars_populated_by_init", "Pop. Init"),
        ("vars_required_for_update", "Req. Update"),
        ("vars_populated_by_first_update", "Pop. Update"),
        ("vars_updated", "Updated"),
    )

    variable_attributes = {v[1]: [] for v in model_var_attribute_fields}

    # Order the dictionary fields in the eventual desired table field order
    field_order = ["name", "unit", "axis", "description", "variable_type"]

    # Build the source data into a dictionary of variables in the right field order and
    # with the additional usage fields.
    known_vars = {}
    for var in source_vars:
        new_var = {f: var[f] for f in field_order}
        new_var.update(deepcopy(variable_attributes))
        known_vars[var["name"]] = new_var

    # Iterate over the models, getting the variables associated with each usage type and
    # then adding the model name to the appropriate variable usage lists.
    for this_model in models:
        for var_attr, field_name in model_var_attribute_fields:
            vars = getattr(this_model, var_attr)

            for var_name in vars:
                known_vars[var_name][field_name].append(this_model.model_name)

    # Get a table head using DataTables classes that control the logic of how columns
    # are handled by Responsive wrapping of columns
    # * all: always shown
    # * none: always wrapped in details
    # * never: not shown at all  (but still searchable and filterable)

    table_column_data = {
        "control": {"class": "dt-control", "field": "Name"},
        "name": {"class": "all", "field": "Name"},
        "units": {"class": "all", "field": "Units"},
        "axes": {"class": "none", "field": "Axes"},
        "description": {"class": "none", "field": "Description"},
        "type": {"class": "none", "field": "Variable Type"},
        "vars_required_for_init": {"class": "never", "field": "Req. Init"},
        "vars_populated_by_init": {"class": "never", "field": "Pop. Init"},
        "vars_required_for_update": {"class": "never", "field": "Req. Update"},
        "vars_populated_by_first_update": {"class": "never", "field": "Pop. Update"},
        "vars_updated": {"class": "never", "field": "Updated"},
    }

    thead = dt.thead(
        dt.tr(
            [dt.th(v["field"], _class=v["class"]) for v in table_column_data.values()]
        )
    )

    # Populate TR elements for each variable, adding an initial empty column with class
    # dt-control that will be used by DataTables to contain the responsive child row
    # holding the data from the rows marked with `class="none"` above.

    tbody = dt.tbody()
    for var in known_vars.values():
        tbody += dt.tr(
            [
                dt.td(),
                *[
                    dt.td(v if isinstance(v, str) else ",".join(v))
                    for v in var.values()
                ],
            ]
        )

    table = dt.table(thead, tbody, id="variableTable")

    # Generate toggle button groups to select model and variable timing subsets and then
    # insert those into a card
    model_buttons = dt.div(
        dt.button(
            dt.strong("Model:"), type="button", _class="btn btn-danger", disabled=True
        ),
        *(
            (
                dt.input_(
                    type="checkbox",  # checkbox toggle behaviour
                    _class="btn-check",  # bootstrap button styling,
                    id=mod,
                    value=mod,
                    name="models",  # Used to gather checked status of all model buttons
                ),
                dt.label(mod, _for=mod, _class="btn btn-outline-danger"),
            )
            for mod in [m.model_name for m in models]
        ),
        _class="btn-group",
        role="group",
    )

    init_buttons = dt.div(
        dt.button(
            dt.strong("Setup:"), type="button", _class="btn btn-primary", disabled=True
        ),
        (
            dt.input_(type="checkbox", _class="btn-check", id="vars_required_for_init"),
            dt.label(
                "Required",
                _for="vars_required_for_init",
                _class="btn btn-outline-primary",
            ),
        ),
        (
            dt.input_(type="checkbox", _class="btn-check", id="vars_populated_by_init"),
            dt.label(
                "Populated",
                _for="vars_populated_by_init",
                _class="btn btn-outline-primary",
            ),
        ),
        _class="btn-group",
        style="margin-top: 16px;",
        role="group",
    )

    update_buttons = dt.div(
        dt.button(
            dt.strong("Update:"), type="button", _class="btn btn-success", disabled=True
        ),
        (
            dt.input_(
                type="checkbox", _class="btn-check", id="vars_required_for_update"
            ),
            dt.label(
                "Required",
                _for="vars_required_for_update",
                _class="btn btn-outline-success",
            ),
        ),
        (
            dt.input_(
                type="checkbox", _class="btn-check", id="vars_populated_by_first_update"
            ),
            dt.label(
                "Populated",
                _for="vars_populated_by_first_update",
                _class="btn btn-outline-success",
            ),
        ),
        (
            dt.input_(type="checkbox", _class="btn-check", id="vars_updated"),
            dt.label("Updated", _for="vars_updated", _class="btn btn-outline-success"),
        ),
        _class="btn-group",
        style="margin-top: 16px;",
        role="group",
    )

    filters_card = dt.div(
        dt.h5("Filter variables", _class="card-header"),
        dt.div(
            model_buttons,
            init_buttons,
            update_buttons,
            _class="card-body",
        ),
        _class="card",
    )

    # Return the HTML
    return filters_card.render() + table.render()
