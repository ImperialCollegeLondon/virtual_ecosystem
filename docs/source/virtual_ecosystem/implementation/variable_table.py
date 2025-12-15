"""Provides python functions to generate the variable table."""

import tomllib
from copy import deepcopy
from importlib import resources

from virtual_ecosystem.core.variables import _discover_models


def variable_table():
    """Generate an HTML TABLE representation of the data variables.

    This function returns HTML with the following elements:

    * A TABLE element containing the following data on the model variables:
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
        ("vars_required_for_init", "Req Init"),
        ("vars_populated_by_init", "Pop Init"),
        ("vars_required_for_update", "Req Update"),
        ("vars_populated_by_first_update", "Pop Update 1"),
        ("vars_updated", "Updates"),
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
        new_var["Used By"] = set()
        known_vars[var["name"]] = new_var

    # Iterate over the models, getting the variables associated with each usage type and
    # then adding the model name to the appropriate variable usage lists.
    for this_model in models:
        for var_attr, field_name in model_var_attribute_fields:
            vars = getattr(this_model, var_attr)

            for var_name in vars:
                known_vars[var_name][field_name].append(this_model.model_name)
                known_vars[var_name]["Used By"].add(this_model.model_name)

    # Get the row headers - this is hard coded because the individual columns use
    # DataTables responsive class logic to control which fields are visible, which are
    # responsively wrapped into details and which are hidden (but still searchable and
    # filterable)
    # * all: always shown
    # * none: always wrapped in details
    # * never: not shown at all

    thead = """
    <THEAD>
        <TR>
            <TH class="dt-control"</TH>
            <TH class="all">Name</TH>
            <TH class="all">Units</TH>
            <TH class="none">Axes</TH>
            <TH class="none">Description</TH>
            <TH class="none">Variable Type</TH>
            <TH class="never">Req Init</TH>
            <TH class="never">Pop Init</TH>
            <TH class="never">Req Update</TH>
            <TH class="never">Pop Update 1</TH>
            <TH class="never">Updated</TH>
            <TH class="never">Used By</TH>
        </TR>
    </THEAD>
    """

    # Populate TR elements for each variable, adding an initial empty column with class
    # dt-control that will be used by DataTables to contain the responsive child row
    # holding the data from the rows marked with `class="none"` above.
    table_rows = []

    for var in known_vars.values():
        td_elements = [
            "<TD></TD>",
            *[
                f"<TD>{v if isinstance(v, str) else ','.join(v)}</TD>"
                for v in var.values()
            ],
        ]
        table_rows.append(f"<TR>{''.join(td_elements)}</TR>")

    # Add checkbox sets to power subsetting variables by model usage
    model_selector = _generate_checkbox_set("models", [m.model_name for m in models])
    var_group_selector = _generate_checkbox_set(
        "var_group", list(variable_attributes.keys())
    )

    # Return the HTML
    return f"""
    <DIV style="border:1px solid black;padding:4px;">
    {model_selector}
    </DIV>
    <DIV style="border:1px solid black;padding:4px;">
    {var_group_selector}
    </DIV>
    <TABLE id='variableTable'>
    {thead}
    <TBODY>
    {"".join(table_rows)}
    </TBODY>
    </TABLE>
    """


def _generate_checkbox_set(id: str, values: list[str]):
    input_list = [
        f"""
        <div style="display:flex;margin:2px;">
            <input type="checkbox" name="{id}" id={id + "-" + v} value="{v}">
            <label for="{id + "-" + v}">{v}</label>
        </div>
        """
        for v in values
    ]
    inputs = "\n".join(input_list)
    return f"""
        <div style="display:flex;" id="{id}">\n{inputs}
        </div>
    """
