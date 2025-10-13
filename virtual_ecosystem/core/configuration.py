"""Configuration system elements for pydantic."""

from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, FilePath
from pydantic._internal._model_construction import ModelMetaclass


class ModelConfigRoot(BaseModel):
    """Root configuration class for models.

    This model provides a common `pydantic` base class to be used as the root for the
    model configuration in all model implementations. Each model must define a
    single class inheriting from :class:`ModelConfigRoot` in the ``model_config.py``
    submodule. The file can then include other :class:`ModelConfigSection` classes that
    are used within the root configuration but there must be a single root model
    configuration class.

    The base model defines the shared ``static`` option for each model and also sets
    common configuration options.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    static: bool = False
    """The model static mode setting."""


class ModelConfigSection(BaseModel):
    """Section configuration class for models.

    This model provides a common base class for subsections within model configurations.
    all model implementations. The base model currently just defines common
    configuration options.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)


def placeholder_validator(path: str) -> str:
    """A custom validator to reject "<PLACEHOLDER>" when loading file paths."""
    if path == "<PLACEHOLDER>":
        raise ValueError("Path placeholder value in configuration.")

    return path


FILEPATH_PLACEHOLDER: TypeAlias = Annotated[
    FilePath,
    Field(default=Path("<PLACEHOLDER>")),
    BeforeValidator(placeholder_validator),
]
"""Pydantic type that provides a default '<PLACEHOLDER>' text for writing configuration
templates, but screens input before the standard validation to refuse unreplaced
placeholder values. The type then uses FilePath, which validates that a path actually
exists on the file system. The field does not set ``validate_defaults`` so the
placeholder value can be written despite not being an existing file.

.. TODO: Fix autodoc
    This generates a bizarre set of autodoc link failures that generate random text 
    chunks from the Annotator pattern. Currently tackled using nitpick ignore.
"""


def model_markdown_description(
    model_name: str, model_config: type[Any], mode: Literal["dl", "tr"] = "tr"
) -> str:
    """Render the fields in a ModelConfig class as Markdown.

    The function recurses through sub-models within a ModelConfig instance and generates
    a definition list entry for each configuration setting. If rendered for display
    inside a MyST markdown code cell, the notebook will need to be set to render
    markdown from code cells using MyST rather than the default CommonMark.

    .. code-block:: yaml

        mystnb:
            render_markdown_format: myst

    Args:
        model_name: The name of the model as it would appear in a configuration file.
        model_config: The ModelConfig instance for a model
        mode: A selector for the kind of formatted output.
    """
    if mode == "dl":
        output = "\n\n"
        for name, field_info in model_config.model_fields.items():
            field_name = model_name + "." + name
            if isinstance(field_info.annotation, ModelMetaclass):
                output += (
                    f"[{field_name}]\n: Config section: {field_info.description}\n\n"
                )
                output += model_markdown_description(
                    field_name, field_info.annotation, mode=mode
                )
            else:
                output += (
                    f"[{field_name}]\n: {field_info.description} "
                    f"Default = {field_info.default}\n\n"
                )
        output += "\n\n"

    if mode == "tr":
        # An attempt at producing a table - needs more thought. Using HTML to
        # potentially support colspan, which no easy markdown table formats provide.
        output = f"<tr><td>{model_name}</td><td>{model_config.__doc__}</td></tr>"

        for name, field_info in model_config.model_fields.items():
            field_name = model_name + "." + name
            if isinstance(field_info.annotation, ModelMetaclass):
                output += (
                    f"<tr><td>{field_name}</td><td>Config "
                    f"section: {field_info.description}</td></tr>"
                )
                output += model_markdown_description(
                    field_name, field_info.annotation, mode=mode
                )
            else:
                output += (
                    f"<tr><td>{field_name}</td><td>{field_info.description}, "
                    f"Default = {field_info.default}</td></tr>"
                )

    return output
