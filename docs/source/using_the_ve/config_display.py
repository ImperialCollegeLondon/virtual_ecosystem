"""Helper functions for displaying configuration object TOML and definitions."""

from textwrap import indent

import tomli_w
from IPython.display import display_markdown
from pydantic._internal._model_construction import ModelMetaclass
from pydantic_core import PydanticUndefined

from virtual_ecosystem.core.configuration import Configuration

RST_TO_MD = [
    (":cite:t:", "{cite:t}"),
    (":cite:p:", "{cite:p}"),
    (":attr:", "{attr}"),
]
"""Tags to replace when converting RST descriptions of fields to Markdown."""


def dump_config_toml(path: str, config_class: type[Configuration]) -> None:
    """Render a configuration class as TOML.

    This function returns markdown providing a styled TOML representation of a
    Configuration subclass, including default values.

    Args:
        path: The configuration path to the specified configuration class.
        config_class: The configuration class to express as TOML.
    """

    conf_dict = config_class().model_dump(mode="json")

    for p in reversed(path.split(".")):
        conf_dict = {p: conf_dict}

    display_markdown("```toml\n" + tomli_w.dumps(conf_dict) + "```")


def model_config_to_deflist(
    model_name: str,
    config_object: type[Configuration],
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
