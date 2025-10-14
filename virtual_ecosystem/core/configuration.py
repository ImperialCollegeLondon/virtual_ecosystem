"""Configuration system elements for pydantic."""

from pathlib import Path
from typing import Annotated, TypeAlias

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, FilePath
from pydantic._internal._model_construction import ModelMetaclass
from pydantic_core import PydanticUndefined


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


class ModelConfigHTMLTable:
    """Class to render the fields in a ModelConfig class as an HTML Table.

    The function recurses through sub-models within a ModelConfig instance and generates
    a simple HTML table showing the config sections and then the description and
    defaults of each setting.

    Args:
        model_name: The name of the model as it would appear in a configuration file.
        config_object: A ModelConfig instance
    """

    def __init__(
        self,
        model_name: str,
        config_object: type[ModelConfigRoot] | type[ModelConfigSection],
    ):
        # Initialise a list of rows
        self.rows: list[str] = []

        # Add the section header as a row with dark background
        self.rows += [
            f"<tr><td style='background-color:#c9c9c9;text-align:left;'>"
            f"<strong>[{model_name}]</strong></td></tr>",
        ]

        # Iterate over the model fields
        for name, field_info in config_object.model_fields.items():
            # Track the nested name of the field
            field_name = model_name + "." + name

            if isinstance(field_info.annotation, ModelMetaclass):
                # If the field is itself a model, then this is a nested section, so
                # recurse into the model and then append the collected rows to the
                # parent instance
                self.rows += ModelConfigHTMLTable(
                    field_name, field_info.annotation
                ).rows

            else:
                # Otherwise, get the default value (or not) for the field
                default = field_info.get_default(call_default_factory=True)

                if default is PydanticUndefined:
                    default_string = "No default"
                else:
                    default_string = f"Default ={default!s}"

                description = (
                    "Field description missing."
                    if field_info.description is None
                    else field_info.description
                )

                self.rows += [
                    f"<tr><td style='text-align:left;background-color:#e3e3e3;'>"
                    f"<strong>[{field_name}]</strong></td></tr>",
                    f"<tr><td style='text-align:left;background-color:white;'>"
                    f"{description}. {default_string}</td></tr>",
                ]

    def get_table(self) -> str:
        """Return a compiled ModelConfig table as HTML."""
        return "<table><tbody>" + "".join(self.rows) + "<tbody><table>"
