"""The :mod:`~virtual_ecosystem.core.configuration` module provides the core
model configuration elements for the Virtual Ecosystem. It defines shared pydantic base
classes that are used to define configuration settings for a model.

Each model must define an object ``model_name.model_config.ModelConfiguration``. For the
science models, this object **must** inherit from :class:`ModelConfigurationRoot`, which
provides the common ``static`` setting. The `core.model_config.ModelConfiguration`
configuration instead directly uses :class:`Configuration` since it cannot be run in
static mode. The ``model_name.model_config`` module can then include other
:class:`Configuration` classes that are used as nested fields within the root
configuration class.

The basic details of how this system is used can be
found :doc:`here </using_the_ve/configuration/config>`.
"""  # noqa: D205

from pathlib import Path
from typing import Annotated, TypeAlias

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, FilePath
from pydantic._internal._model_construction import ModelMetaclass
from pydantic_core import PydanticUndefined

RST_TO_MD = [
    (":cite:t:", "{cite:t}"),
    (":cite:p:", "{cite:p}"),
    (":attr:", "{attr}"),
]
"""Tags to replace when converting RST descriptions of fields to Markdown."""


class Configuration(BaseModel):
    """Base configuration class for the Virtual Ecosystem.

    This model provides a common Pydantic base class for use in configuring the
    Virtual Ecosystem. This base class is used to share common configuration settings
    for all models. It is also used as the root configuration base for the core
    configuration settings.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)


class CompiledConfiguration(Configuration):
    """Compiled configuration class for Virtual Ecosystem models.

    This class is used as the base for dynamically compiled complete model returned by
    the ``ConfigurationLoader(...).get_configuration()`` method. It provides a shared
    method to extract specific model configurations by name. This is needed because the
    dynamic creation means that model fields are not explicitly declared, so `mypy` gets
    does not handle ``configuration.plants``, but we can use
    `configuration.get_subconfiguration("plants")` instead.
    """

    def get_subconfiguration(self, name: str) -> Configuration:
        """Get a named subconfiguration object from a compiled configuration.

        This method can be used to extract model configurations or the core
        configuration from a compiled configuration instance.

        Args:
            name: The required subconfiguration.
        """

        try:
            return getattr(self, name)
        except AttributeError:
            raise AttributeError(f"Model configuration for {name} not loaded")


class ModelConfigurationRoot(Configuration):
    """Root configuration class for individual Virtual Ecosystem models.

    This model provides a common Pydantic base class that must be used to define
    the root configuration class of a Virtual Ecosystem model. Each model must define an
    object ``model_name.model_config.ModelConfiguration`` that inherits from
    :class:`ModelConfigurationRoot`. The ``model_name.model_config`` module
    can then include other :class:`Configuration` classes that
    are used as nested fields within the root configuration but can be only one
    :class:`ModelConfigurationRoot` class per model. This base model sets common shared
    attributes across models: currently just the shared ``static`` option.
    """

    static: bool = False
    """The model static mode setting."""


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
    This generates a bizarre set of autodoc link failures that try and build links from
    the text elements from the Annotated pattern. Currently tackled using nitpick 
    ignore.
"""


def model_config_to_html(
    model_name: str, config_object: type[Configuration], rows_only: bool = False
):
    """Renders the fields in a model configuration class as an HTML Table.

    This is a helper function for use in documenting model configurations. It takes a
    model configuration class and then iterates over model fields, recursing into
    sub-models within the fields, to generate a simple HTML table showing the config
    sections and then the description and defaults of each setting. The CSS classes are
    defined in ``docs/source/_static/css/custom.css``.

    Args:
        model_name: The name of the model as it would appear in a configuration file.
        config_object: A ModelConfig instance
        rows_only: Should the function wrap the returned rows with HTML table and tbody
            tags?
    """

    # Start with the section header
    rows = (
        f"<tr class='config-section'><td class='element-name'>[{model_name}]</td></tr>"
    )

    # Iterate over the model fields
    for name, field_info in config_object.model_fields.items():
        # Track the nested name of the field
        field_name = model_name + "." + name

        if isinstance(field_info.annotation, ModelMetaclass):
            # If the field is itself a model, then this is a nested section, so
            # recurse into the model and then append the collected rows to the
            # parent instance
            rows += model_config_to_html(
                field_name, field_info.annotation, rows_only=True
            )

        else:
            # Otherwise, get the default value (or not) for the field
            default = field_info.get_default(call_default_factory=True)

            if default is PydanticUndefined:
                default_string = "No default"
            else:
                default_string = f"Default ={default!s}"

            if field_info.description is None:
                description = "Field description missing."
            else:
                description = field_info.description
                for rst, md in RST_TO_MD:
                    description = description.replace(rst, md)

            rows += (
                f"<tr class='config-element'>"
                f"<td class='element-name'>[{field_name}]</td></tr>"
                f"<tr class='config-desc'><td class='config-desc'>"
                f"{description} {default_string}</td></tr>"
            )

    if rows_only:
        return rows

    return "<table><tbody>" + rows + "<tbody><table>"
