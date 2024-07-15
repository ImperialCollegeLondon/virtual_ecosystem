"""Utility functions to generate model variable listings."""

from virtual_ecosystem.core import variables


def generate_variable_listing(model_name: str, var_attributes: list[str]) -> str:
    """Generate variable listings for a model."""

    # populate the known variables registry if empty
    if not variables.KNOWN_VARIABLES:
        variables.register_all_variables()

    # Find the model reference
    models = {m.__name__: m for m in variables._discover_models()}
    if model_name not in models:
        raise ValueError("Unknown model name")
    model = models[model_name]

    # Define listing headings for each attribute:
    vattr_headings = {
        "vars_required_for_init": "Variables required to initialise the model",
        "vars_updated": "Variables updated by the model",
        "vars_required_for_update": "Variables required to update the model",
        "vars_populated_by_init": "Variables populated by initialising the model",
        "vars_populated_by_first_update": "Variables by the first update of the model",
    }

    # Collect the listings for each requested variable attribute into a string
    return_value = ""

    for vattr in var_attributes:
        # Trap bad attributes
        if vattr not in vattr_headings:
            raise ValueError("Unknown variable attribute")

        # Get the listing
        listing = "\n".join(
            [
                f"* {v.description} (``{v.name}``, {v.unit})"
                for k, v in variables.KNOWN_VARIABLES.items()
                if k in getattr(model, vattr)
            ]
        )
        # Add listing
        return_value += f"\n**{vattr_headings[vattr]}**\n{listing}"

    return return_value


def generate_variable_table(model_name: str, var_attributes: list[str]) -> str:
    """Generate variable listings for a model."""

    # populate the known variables registry if empty
    if not variables.KNOWN_VARIABLES:
        variables.register_all_variables()

    # Find the model reference
    models = {m.__name__: m for m in variables._discover_models()}
    if model_name not in models:
        raise ValueError("Unknown model name")
    model = models[model_name]

    # Define listing headings for each attribute:
    vattr_headings = {
        "vars_required_for_init": "Variables required to initialise the model",
        "vars_updated": "Variables updated by the model",
        "vars_required_for_update": "Variables required to update the model",
        "vars_populated_by_init": "Variables populated by initialising the model",
        "vars_populated_by_first_update": (
            "Variables populated by the first model update"
        ),
    }

    # Collect the listings for each requested variable attribute into a string
    return_value = ""

    for vattr in var_attributes:
        # Trap bad attributes
        if vattr not in vattr_headings:
            raise ValueError("Unknown variable attribute")

        # Get the variables formatted as list table rows
        listing = "\n".join(
            [
                f"* - `{v.name}`\n  - {v.description}\n  - {v.unit}"
                for k, v in variables.KNOWN_VARIABLES.items()
                if k in getattr(model, vattr)
            ]
        )

        # Wrap the variable rows in the rest of the list table syntax
        table = (
            ":::{list-table}\n"
            + ':header-rows: 1\n:widths: 30 40 10\n:width: 100%\n:align: "left"\n\n'
            + "* - Name\n  - Description\n  - Unit\n"
            + listing
            + "\n:::\n"
        )
        return_value += f"\n**{vattr_headings[vattr]}**\n\n{table}"

    return return_value
